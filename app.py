from config.settings import (
    ApplicationConfig,
    create_required_directories,
    validate_environment,
)

create_required_directories()

print("=" * 50)
print(ApplicationConfig.APP_NAME)
print(ApplicationConfig.VERSION)
print(ApplicationConfig.DESCRIPTION)
print("=" * 50)

status, message = validate_environment()

print(status)
print(message)