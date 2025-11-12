.PHONY: schema schema-only

# Generate OpenAPI schema and update frontend
schema:
	cd app && python manage.py spectacular --file ../openapi-schema.yaml --validate
	cd ../frontend_bridge && flutter pub run build_runner build --delete-conflicting-outputs

# Just generate schema without frontend update
schema-only:
	cd app && python manage.py spectacular --file ../openapi-schema.yaml --validate
