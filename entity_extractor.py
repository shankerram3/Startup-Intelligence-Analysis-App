"""
Entity and Relationship Extraction for TechCrunch Articles
Based on GraphRAG approach - extracts entities and relationships from article text
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Add parent directory to path for utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.checkpoint import CheckpointManager
from utils.data_validation import validate_article, validate_extraction
from utils.entity_normalization import normalize_entity_name
from utils.filter_techcrunch import (
    filter_techcrunch_entities,
    filter_techcrunch_relationship,
)
from utils.progress_tracker import ProgressTracker
from utils.retry import retry_with_backoff


class TechCrunchEntityExtractor:
    """Extract entities and relationships from TechCrunch articles"""

    def __init__(self, openai_api_key: str, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(temperature=0.0, model=model, api_key=openai_api_key)

        # Entity extraction prompt (adapted from GraphRAG notebook)
        self.entity_extraction_prompt = """
-Goal-
Given a TechCrunch article text, identify all entities of specified types and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [company, person, investor, technology, product, funding_round, location, event]
- entity_description: Comprehensive description of the entity's attributes and activities

Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_type: One of: [FUNDED_BY, FOUNDED_BY, WORKS_AT, ACQUIRED, PARTNERS_WITH, COMPETES_WITH, USES_TECHNOLOGY, LOCATED_IN, ANNOUNCED_AT, REGULATES, OPPOSES, SUPPORTS, COLLABORATES_WITH, INVESTS_IN, ADVISES, LEADS]
Note: Do NOT create MENTIONED_IN relationships - entity-to-article relationships are handled separately

Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_type>{tuple_delimiter}<relationship_strength>)

3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

4. When finished, output {completion_delimiter}

-Examples-
######################

Example 1:

Entity_types: company, person, investor, technology, funding_round
Text:
Anthropic, an AI safety startup founded by former OpenAI researchers Dario Amodei and Daniela Amodei, announced today it has raised $450 million in Series C funding led by Spark Capital. The round values the company at $4.1 billion. Anthropic's flagship product, Claude, competes directly with OpenAI's ChatGPT in the large language model space.
######################
Output:
("entity"{tuple_delimiter}ANTHROPIC{tuple_delimiter}company{tuple_delimiter}Anthropic is an AI safety startup valued at $4.1 billion, known for its flagship product Claude)
{record_delimiter}
("entity"{tuple_delimiter}DARIO AMODEI{tuple_delimiter}person{tuple_delimiter}Dario Amodei is a former OpenAI researcher who co-founded Anthropic)
{record_delimiter}
("entity"{tuple_delimiter}DANIELA AMODEI{tuple_delimiter}person{tuple_delimiter}Daniela Amodei is a former OpenAI researcher who co-founded Anthropic)
{record_delimiter}
("entity"{tuple_delimiter}SPARK CAPITAL{tuple_delimiter}investor{tuple_delimiter}Spark Capital is a venture capital firm that led Anthropic's Series C funding round)
{record_delimiter}
("entity"{tuple_delimiter}SERIES C FUNDING{tuple_delimiter}funding_round{tuple_delimiter}Series C funding round of $450 million for Anthropic)
{record_delimiter}
("entity"{tuple_delimiter}CLAUDE{tuple_delimiter}product{tuple_delimiter}Claude is Anthropic's flagship product, a large language model)
{record_delimiter}
("entity"{tuple_delimiter}OPENAI{tuple_delimiter}company{tuple_delimiter}OpenAI is an AI company that previously employed Anthropic's founders)
{record_delimiter}
("entity"{tuple_delimiter}CHATGPT{tuple_delimiter}product{tuple_delimiter}ChatGPT is OpenAI's large language model product that competes with Claude)
{record_delimiter}
("relationship"{tuple_delimiter}ANTHROPIC{tuple_delimiter}DARIO AMODEI{tuple_delimiter}Dario Amodei co-founded Anthropic{tuple_delimiter}FOUNDED_BY{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}ANTHROPIC{tuple_delimiter}DANIELA AMODEI{tuple_delimiter}Daniela Amodei co-founded Anthropic{tuple_delimiter}FOUNDED_BY{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}ANTHROPIC{tuple_delimiter}SPARK CAPITAL{tuple_delimiter}Spark Capital led Anthropic's $450M Series C funding round{tuple_delimiter}FUNDED_BY{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}ANTHROPIC{tuple_delimiter}CLAUDE{tuple_delimiter}Claude is Anthropic's flagship product{tuple_delimiter}USES_TECHNOLOGY{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}DARIO AMODEI{tuple_delimiter}OPENAI{tuple_delimiter}Dario Amodei previously worked at OpenAI{tuple_delimiter}WORKS_AT{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}DANIELA AMODEI{tuple_delimiter}OPENAI{tuple_delimiter}Daniela Amodei previously worked at OpenAI{tuple_delimiter}WORKS_AT{tuple_delimiter}8)
{record_delimiter}
("relationship"{tuple_delimiter}CLAUDE{tuple_delimiter}CHATGPT{tuple_delimiter}Claude competes directly with ChatGPT in the LLM space{tuple_delimiter}COMPETES_WITH{tuple_delimiter}9)
{completion_delimiter}

#############################

-Real Data-
######################
Entity_types: company, person, investor, technology, product, funding_round, location, event
Text: {input_text}
######################
Output:
"""

        # Delimiters (from GraphRAG)
        self.tuple_delimiter = "<|>"
        self.record_delimiter = "##"
        self.completion_delimiter = "<|COMPLETE|>"

    def extract_from_article(self, article_data: Dict) -> Dict:
        """
        Extract entities and relationships from a single article

        Args:
            article_data: Dict with 'content' (headline, paragraphs) and 'metadata'

        Returns:
            Dict with entities, relationships, and metadata
        """
        # Combine headline and paragraphs
        headline = article_data["content"]["headline"]
        paragraphs = article_data["content"]["paragraphs"]

        # Create text for extraction (limit to reasonable size)
        full_text = f"{headline}\n\n" + "\n".join(
            paragraphs[:20]
        )  # First 20 paragraphs

        # Extract entities and relationships
        entities, relationships = self._extract_entities_relationships(full_text)

        return {
            "article_metadata": article_data["metadata"],
            "entities": entities,
            "relationships": relationships,
            "extraction_timestamp": datetime.now().isoformat(),
        }

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        exceptions=(Exception,),
    )
    def _extract_entities_relationships(
        self, text: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """Use LLM to extract entities and relationships with retry logic"""

        # Create prompt
        prompt = ChatPromptTemplate.from_template(self.entity_extraction_prompt)

        # Create chain
        chain = prompt | self.llm | StrOutputParser()

        # Run extraction
        result = chain.invoke(
            {
                "input_text": text,
                "tuple_delimiter": self.tuple_delimiter,
                "record_delimiter": self.record_delimiter,
                "completion_delimiter": self.completion_delimiter,
            }
        )

        # Parse the result
        entities, relationships = self._parse_extraction_result(result)

        # Filter out TechCrunch/Disrupt entities (additional check)
        filtered_entities, filtered_names = filter_techcrunch_entities(entities)
        if filtered_names:
            print(
                f"  ⚠️  Filtered out {len(filtered_names)} TechCrunch/Disrupt entities: {', '.join(filtered_names[:5])}{'...' if len(filtered_names) > 5 else ''}"
            )
        entities = filtered_entities

        # Normalize entity names
        entities = self._normalize_entities(entities)

        return entities, relationships

    def _normalize_entities(self, entities: List[Dict]) -> List[Dict]:
        """Normalize entity names to reduce duplicates"""
        for entity in entities:
            if "name" in entity:
                original_name = entity["name"]
                entity["normalized_name"] = normalize_entity_name(original_name)
                # Keep original name but add normalized version for matching
        return entities

    def _parse_extraction_result(self, result: str) -> Tuple[List[Dict], List[Dict]]:
        """Parse the LLM output into structured entities and relationships"""

        entities = []
        relationships = []

        # Remove completion delimiter
        result = result.replace(self.completion_delimiter, "")

        # Split by record delimiter
        records = result.split(self.record_delimiter)

        for record in records:
            record = record.strip()
            if not record:
                continue

            # Parse entity
            if record.startswith('("entity"'):
                entity = self._parse_entity(record)
                if entity:
                    # Filter out TechCrunch/Disrupt related entities
                    from utils.filter_techcrunch import filter_techcrunch_entity

                    should_filter, reason = filter_techcrunch_entity(entity)
                    if should_filter:
                        print(
                            f"  ⚠️  Filtered out TechCrunch/Disrupt entity: {entity.get('name', '?')}"
                        )
                        continue
                    entities.append(entity)

            # Parse relationship
            elif record.startswith('("relationship"'):
                relationship = self._parse_relationship(record)
                if relationship:
                    # Filter out MENTIONED_IN relationships at parse time
                    rel_type = relationship.get("type", "")
                    if rel_type == "MENTIONED_IN":
                        print(
                            f"  ⚠️  Filtered out MENTIONED_IN relationship from {relationship.get('source', '?')} to {relationship.get('target', '?')}"
                        )
                        continue  # Skip MENTIONED_IN relationships

                    # Filter out relationships involving TechCrunch/Disrupt entities
                    should_filter, reason = filter_techcrunch_relationship(relationship)
                    if should_filter:
                        print(
                            f"  ⚠️  Filtered out TechCrunch/Disrupt relationship: {reason}"
                        )
                        continue

                    relationships.append(relationship)

        return entities, relationships

    def _parse_entity(self, record: str) -> Dict:
        """Parse entity record"""
        try:
            # Extract content between parentheses
            content = record[record.find("(") + 1 : record.rfind(")")]

            # Split by delimiter
            parts = content.split(self.tuple_delimiter)

            if len(parts) >= 4:
                return {
                    "name": parts[1].strip(),
                    "type": parts[2].strip(),
                    "description": parts[3].strip(),
                }
        except Exception as e:
            print(f"Error parsing entity: {e}")

        return None

    def _parse_relationship(self, record: str) -> Dict:
        """Parse relationship record"""
        try:
            # Extract content between parentheses
            content = record[record.find("(") + 1 : record.rfind(")")]

            # Split by delimiter
            parts = content.split(self.tuple_delimiter)

            if len(parts) >= 6:
                return {
                    "source": parts[1].strip(),
                    "target": parts[2].strip(),
                    "description": parts[3].strip(),
                    "type": parts[4].strip(),
                    "strength": (
                        int(parts[5].strip()) if parts[5].strip().isdigit() else 5
                    ),
                }
        except Exception as e:
            print(f"Error parsing relationship: {e}")

        return None


def load_article_data(json_path: str) -> Dict:
    """Load and extract relevant data from scraped article JSON"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle case where file contains a list (metadata files should be filtered out earlier)
    if isinstance(data, list):
        raise ValueError(
            f"File {json_path} contains a list, not an article object. This should be a metadata file."
        )

    # Validate it's a dictionary with required fields
    if not isinstance(data, dict):
        raise ValueError(f"File {json_path} does not contain a valid article object.")

    # Check for required fields
    if "content" not in data or "article_id" not in data:
        raise ValueError(
            f"File {json_path} is missing required fields (content or article_id)."
        )

    return {
        "content": {
            "headline": data["content"]["headline"],
            "paragraphs": data["content"]["paragraphs"],
        },
        "metadata": {
            "url": data.get("url", ""),
            "title": data.get("title", ""),
            "published_date": data.get("published_date", ""),
            "article_id": data["article_id"],
        },
    }


def process_articles_directory(
    articles_dir: str,
    output_dir: str,
    openai_api_key: str,
    max_articles: int = None,
    resume: bool = True,
    validate_data: bool = True,
):
    """
    Process all articles in a directory and extract entities/relationships

    Args:
        articles_dir: Path to directory containing article JSON files
        output_dir: Path to save extracted entities/relationships
        openai_api_key: OpenAI API key
        max_articles: Optional limit on number of articles to process
        resume: Resume from checkpoint if available
        validate_data: Validate articles before processing
    """

    extractor = TechCrunchEntityExtractor(openai_api_key)

    # Find all JSON files, excluding metadata files
    articles_path = Path(articles_dir)

    # Get all JSON files but exclude metadata directory and metadata files
    json_files = []
    for json_file in articles_path.rglob("*.json"):
        # Skip metadata directory
        if "metadata" in json_file.parts:
            continue
        # Skip metadata files (discovered_articles, failed_articles, checkpoints, etc.)
        if any(
            pattern in json_file.name
            for pattern in [
                "discovered_articles_",
                "failed_articles_",
                "extraction_checkpoint_",
                "scraping_stats_",
                "discovery_checkpoint_",
            ]
        ):
            continue
        json_files.append(json_file)

    # Sort by path for consistent processing order
    json_files.sort()

    if max_articles:
        json_files = json_files[:max_articles]

    # Initialize checkpoint manager
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    checkpoint_file = output_path / "extraction_checkpoint.json"
    checkpoint = CheckpointManager(checkpoint_file)

    # Filter out already processed articles if resuming
    if resume:
        original_count = len(json_files)
        json_files = checkpoint.filter_unprocessed(json_files)
        skipped = original_count - len(json_files)
        if skipped > 0:
            print(f"⏭  Resuming: Skipping {skipped} already processed articles")

    print(f"Found {len(json_files)} articles to process")

    # Initialize progress tracker
    progress_tracker = ProgressTracker(
        operation_name="Entity Extraction",
        report_file=output_path / "extraction_progress.json",
    )
    progress_tracker.start(len(json_files))

    # Process each article
    all_extractions = []

    # Track if we actually process any new articles in this run
    new_articles_processed = 0
    
    # Try to load existing extractions if resuming (but only use if we process new articles)
    all_extractions_file = output_path / "all_extractions.json"
    existing_extractions = []
    if resume and all_extractions_file.exists():
        try:
            with open(all_extractions_file, "r", encoding="utf-8") as f:
                existing_extractions = json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing extractions: {e}")
    
    # Start with empty list - only add new extractions
    all_extractions = []

    for i, json_file in enumerate(json_files, 1):
        article_id = None

        try:
            # Load article
            article_data = load_article_data(str(json_file))
            article_id = article_data.get("metadata", {}).get("article_id")

            # Validate article data
            if validate_data:
                is_valid, error_msg = validate_article(article_data)
                if not is_valid:
                    print(
                        f"  ⚠️  Skipping invalid article {json_file.name}: {error_msg}"
                    )
                    progress_tracker.mark_skipped()
                    if article_id:
                        checkpoint.mark_failed(article_id)
                    continue

            # Check if already processed
            if resume and article_id and checkpoint.is_processed(article_id):
                print(f"  ⏭  Skipping already processed: {json_file.name}")
                progress_tracker.mark_skipped()
                continue

            print(f"\n[{i}/{len(json_files)}] Processing: {json_file.name}")

            # Extract entities and relationships
            extraction = extractor.extract_from_article(article_data)

            # Validate extraction
            if validate_data:
                is_valid, errors = validate_extraction(extraction)
                if not is_valid:
                    print(f"  ⚠️  Extraction validation failed: {', '.join(errors)}")
                    # Still save, but mark as having issues
                    progress_tracker.mark_failed(
                        f"Validation errors: {', '.join(errors)}"
                    )

            # Add to collection
            all_extractions.append(extraction)
            new_articles_processed += 1

            # Print summary
            print(f"  ✓ Extracted {len(extraction['entities'])} entities")
            print(f"  ✓ Extracted {len(extraction['relationships'])} relationships")

            # Save individual extraction
            output_file = (
                output_path / f"extraction_{article_id or json_file.stem}.json"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extraction, f, indent=2, ensure_ascii=False)

            # Mark as processed
            if article_id:
                checkpoint.mark_processed(article_id)

            progress_tracker.mark_processed()

            # Save checkpoint periodically (every 10 articles)
            if i % 10 == 0:
                checkpoint.save()
                # Save all extractions incrementally
                with open(all_extractions_file, "w", encoding="utf-8") as f:
                    json.dump(all_extractions, f, indent=2, ensure_ascii=False)

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user. Saving progress...")
            checkpoint.save()
            with open(all_extractions_file, "w", encoding="utf-8") as f:
                json.dump(all_extractions, f, indent=2, ensure_ascii=False)
            progress_tracker.finish()
            progress_tracker.print_summary()
            raise

        except Exception as e:
            print(f"  ✗ Error processing {json_file.name}: {e}")
            progress_tracker.mark_failed(str(e))
            if article_id:
                checkpoint.mark_failed(article_id)
            continue

    # Final save
    checkpoint.save()
    checkpoint_stats = checkpoint.get_stats()

    # Only merge with existing extractions if we processed new articles
    # If no new articles were processed (all were skipped), return empty list
    # This ensures we skip previously processed articles and don't reuse old extractions
    if new_articles_processed > 0:
        # Merge new extractions with existing ones (avoid duplicates)
        if existing_extractions:
            existing_ids = {ext.get("article_metadata", {}).get("article_id") for ext in existing_extractions}
            for ext in all_extractions:
                article_id = ext.get("article_metadata", {}).get("article_id")
                if article_id and article_id not in existing_ids:
                    existing_extractions.append(ext)
                    existing_ids.add(article_id)
            all_extractions = existing_extractions
        
        # Save all extractions (merged if applicable)
        with open(all_extractions_file, "w", encoding="utf-8") as f:
            json.dump(all_extractions, f, indent=2, ensure_ascii=False)
    else:
        # No new articles processed - return empty list to skip old extractions
        print("⚠️  No new articles processed. All articles were already processed.")
        all_extractions = []

    # Finish progress tracking
    progress_tracker.finish()

    print(f"\n{'='*80}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"New articles processed in this run: {new_articles_processed}")
    print(f"Total extractions returned: {len(all_extractions)}")
    print(f"Output directory: {output_path}")
    if checkpoint_stats["processed_count"] > 0:
        print(
            f"Checkpoint: {checkpoint_stats['processed_count']} processed, {checkpoint_stats['failed_count']} failed"
        )
    print(f"{'='*80}\n")

    progress_tracker.print_summary()

    return all_extractions


def main():
    """Example usage"""
    import os

    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ARTICLES_DIR = "data/articles"
    OUTPUT_DIR = "data/processing"

    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    # Process articles (start with just 5 for testing)
    extractions = process_articles_directory(
        articles_dir=ARTICLES_DIR,
        output_dir=OUTPUT_DIR,
        openai_api_key=OPENAI_API_KEY,
        max_articles=5,  # Remove or increase this for full processing
    )

    # Print sample
    if extractions:
        print("\nSample extraction:")
        print(json.dumps(extractions[0], indent=2))


if __name__ == "__main__":
    main()
