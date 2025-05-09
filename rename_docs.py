import os
import re

def to_kebab_case(name):
    # Remove .md extension
    name = name[:-3]
    # Replace underscores with hyphens
    name = name.replace('_', '-')
    # Convert uppercase to lowercase with hyphens
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    # Convert to lowercase
    return s2.lower() + '.md'

# Get all .md files in the docs directory
docs_dir = 'docs'
for filename in os.listdir(docs_dir):
    if filename.endswith('.md'):
        new_name = to_kebab_case(filename)
        if filename != new_name:
            old_path = os.path.join(docs_dir, filename)
            new_path = os.path.join(docs_dir, new_name)
            print(f"Renaming {filename} to {new_name}")
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print(f"Error renaming {filename}: {str(e)}") 