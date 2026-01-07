#!/usr/bin/env python3
import requests

r = requests.get('http://127.0.0.1:8000/api/devices/aliases-db')
aliases = r.json()['aliases']

print("Aliases do tipo host:")
host_aliases = [a for a in aliases if a['alias_type'] == 'host']
for a in host_aliases[:3]:
    print(f"  - {a['name']} (pf_id: {a['pf_id']})")

print("\nAliases do tipo network:")
network_aliases = [a for a in aliases if a['alias_type'] == 'network']
for a in network_aliases[:3]:
    print(f"  - {a['name']} (pf_id: {a['pf_id']})")
