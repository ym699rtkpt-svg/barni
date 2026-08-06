
from __future__ import annotations

import json

from database import database_health, init_database


def main():
    init_database()
    print(json.dumps(database_health(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
