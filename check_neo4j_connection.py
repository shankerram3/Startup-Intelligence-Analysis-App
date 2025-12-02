#!/usr/bin/env python3
"""
Diagnostic script to check Neo4j AuraDB connection
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from neo4j import GraphDatabase
except ImportError:
    print("❌ neo4j package not installed")
    sys.exit(1)

def test_connection():
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USERNAME', os.getenv('NEO4J_USER', 'neo4j'))
    password = os.getenv('NEO4J_PASSWORD')
    
    if not uri:
        print("❌ NEO4J_URI not set in .env")
        return False
    
    if not password:
        print("❌ NEO4J_PASSWORD not set in .env")
        return False
    
    print("=" * 80)
    print("Neo4j AuraDB Connection Diagnostic")
    print("=" * 80)
    print(f"URI: {uri}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    print()
    
    try:
        print("1. Creating driver...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        print("   ✅ Driver created")
        
        print("\n2. Testing basic connectivity...")
        driver.verify_connectivity()
        print("   ✅ Connectivity verified")
        
        print("\n3. Testing read query...")
        with driver.session() as session:
            result = session.run("RETURN 1 as test, datetime() as now")
            record = result.single()
            print(f"   ✅ Read works: test={record['test']}, time={record['now']}")
        
        print("\n4. Testing write query...")
        try:
            with driver.session() as session:
                result = session.run(
                    "CREATE (t:ConnectionTest {id: 'test123', timestamp: timestamp()}) "
                    "RETURN t.id as id, t.timestamp as ts"
                )
                record = result.single()
                print(f"   ✅ Write works: id={record['id']}, timestamp={record['ts']}")
                
                # Clean up
                session.run("MATCH (t:ConnectionTest {id: 'test123'}) DELETE t")
                print("   ✅ Test node cleaned up")
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"   ❌ Write failed: {error_type}: {error_msg}")
            
            if "WriteServiceUnavailable" in error_type or "write service" in error_msg.lower():
                print("\n" + "=" * 80)
                print("DIAGNOSIS: Write Service Unavailable")
                print("=" * 80)
                print("\nPossible causes:")
                print("  1. ⏸️  AuraDB instance is PAUSED/SLEEPING")
                print("     → Go to https://console.neo4j.io/ and check instance status")
                print("     → Resume the instance if it's paused")
                print()
                print("  2. 📊 AuraDB instance is OVER CAPACITY")
                print("     → Check your AuraDB plan limits")
                print("     → Upgrade plan or wait for capacity to free up")
                print()
                print("  3. 🌐 Network connectivity issues")
                print("     → Check firewall rules")
                print("     → Verify DNS resolution")
                print()
                print("  4. 🔄 Connection pool exhausted")
                print("     → Too many concurrent connections")
                print("     → Restart the API container")
                print()
                print("Quick fix: Check AuraDB console at https://console.neo4j.io/")
                return False
        
        print("\n" + "=" * 80)
        print("✅ All connection tests passed!")
        print("=" * 80)
        
        driver.close()
        return True
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"\n❌ Connection failed: {error_type}: {error_msg}")
        
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            print("\n💡 Authentication issue - check your credentials in .env")
        elif "resolve" in error_msg.lower() or "dns" in error_msg.lower():
            print("\n💡 DNS/Network issue - check your internet connection")
        elif "timeout" in error_msg.lower():
            print("\n💡 Timeout - AuraDB instance might be paused or unreachable")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

