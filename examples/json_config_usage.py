"""
Example usage of JSON-based configuration files
Demonstrates how to use the enhanced schema and tenant config with JSON format
"""

from ziora_imports.config.schema_config_json import SchemaConfig
from ziora_imports.config.tenant_config_json import TenantConfig

# Initialize configs (auto-detects JSON or YAML)
schema_config = SchemaConfig()
tenant_config = TenantConfig()

# Example 1: Get schema information with enhanced attributes
object_type = "emp"
schema = schema_config.get_schema(object_type)

if schema:
    print(f"Schema: {schema['display_name']}")
    print(f"Description: {schema['description']}")
    
    # Get field types with enhanced attributes
    field_types = schema_config.get_field_types(object_type)
    print("\nField Types:")
    for field_name, field_info in field_types.items():
        if isinstance(field_info, dict):
            print(f"  {field_name}:")
            print(f"    Type: {field_info.get('type')}")
            print(f"    Length: {field_info.get('length', 'N/A')}")
            print(f"    Required: {field_info.get('required', False)}")
        else:
            print(f"  {field_name}: {field_info}")

# Example 2: Check specific field attributes
field_name = "email"
field_type = schema_config.get_field_type(object_type, field_name)
field_length = schema_config.get_field_length(object_type, field_name)
is_required = schema_config.is_field_required(object_type, field_name)

print(f"\nField '{field_name}':")
print(f"  Type: {field_type}")
print(f"  Length: {field_length}")
print(f"  Required: {is_required}")

# Example 3: Get validation rules
validations = schema_config.get_validations(object_type)
print(f"\nValidations for {object_type}:")
for field, rules in validations.items():
    print(f"  {field}: {rules}")

# Example 4: List tenants
print("\nTenants:")
for tenant_name in tenant_config.list_tenants():
    tenant = tenant_config.get_tenant(tenant_name)
    if tenant:
        print(f"  {tenant_name}: {tenant.display_name} (enabled: {tenant.enabled})")

