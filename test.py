from temp import list_genders

rel_types = list_genders()
for rel_type in rel_types:
    print(f"ID: {rel_type['id']}, Name: {rel_type['name']}")