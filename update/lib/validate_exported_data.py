
import csv
import os
import sys

DBDATA = os.environ["DBDATA"]

csv.field_size_limit(sys.maxsize)  # allow very large fields

def count_fields(field_string: str) -> int:
    """Return the number of comma-separated fields in a string."""
    field_string = field_string.strip()
    if not field_string:
        return 0
    return len(field_string.split(','))

def validate_csv(file_path, expected_fields):
    errors = []
    data_row_count = 0
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, quotechar='"', strict=True)
        header = next(reader, None)
        for lineno, line in enumerate(reader, start=2):
            data_row_count += 1
            try:
                if len(line) != expected_fields:
                    errors.append((lineno, len(line), line))
            except csv.Error as e:
                errors.append((lineno, f"CSV parsing error: {e}"))
    if data_row_count == 0:
        errors.append(("No data rows", 0, "CSV file contains only the header or is empty"))
    return errors

FIELD_COUNTS = {
    "oc_mimetypes.csv": count_fields(os.environ["OC_MIMETYPES_FIELDS"]),
    "oc_mounts.csv": count_fields(os.environ["OC_MOUNTS_FIELDS"]),
    "oc_storages.csv": count_fields(os.environ["OC_STORAGES_FIELDS"]),
    "oc_users.csv": count_fields(os.environ["OC_USERS_FIELDS"]),
    "oc_preferences.csv": count_fields(os.environ["OC_PREFERENCES_FIELDS"]),
    "oc_accounts.csv": count_fields(os.environ["OC_ACCOUNTS_FIELDS"]),
    "oc_accounts_data.csv": count_fields(os.environ["OC_ACCOUNTS_DATA_FIELDS"]),
    "oc_groups.csv": count_fields(os.environ["OC_GROUPS_FIELDS"]),
    "oc_group_user.csv": count_fields(os.environ["OC_GROUP_USER_FIELDS"]),
    "oc_share.csv": count_fields(os.environ["OC_SHARE_FIELDS"]),
    "oc_filecache_extended.csv": count_fields(os.environ["OC_FILECACHE_EXTENDED_FIELDS"]),
    "oc_filecache.csv": count_fields(os.environ["OC_FILECACHE_FIELDS"]),
    "oc_ida_action.csv": count_fields(os.environ["OC_IDA_ACTION_FIELDS"]),
    "oc_ida_frozen_file.csv": count_fields(os.environ["OC_IDA_FROZEN_FILE_FIELDS"]),
    "oc_ida_data_change.csv": count_fields(os.environ["OC_IDA_DATA_CHANGE_FIELDS"]),
}

def main():
    failed = False
    for filename, expected_count in FIELD_COUNTS.items():
        print(f"Validating {filename} (expected field count: {expected_count}) ...")
        csv_file = os.path.join(DBDATA, filename)
        if not os.path.exists(csv_file):
            print(f"Missing CSV file: {csv_file}")
            failed = True
            continue
        errors = validate_csv(csv_file, expected_count)
        if errors:
            print(f"{filename} has field count errors:")
            for err in errors:
                if len(err) == 2:
                    lineno, actual_count = err
                    print(f"Line {lineno}: expected {expected_count}, got {actual_count}")
                elif len(err) == 3:
                    lineno, actual_count, line = err
                    print(f"Line {lineno}: expected {expected_count}, got {actual_count}")
                    print(f"  >> {line}")
            failed = True
    if failed:
        print(f"EXPORTED DATA IS NOT VALID!")
    else:
        print(f"Exported data is OK")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
