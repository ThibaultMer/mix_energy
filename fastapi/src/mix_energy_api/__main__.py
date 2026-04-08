from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("mix_energy_api.main:app", host="0.0.0.0", port=8888, reload=False)


if __name__ == "__main__":
    main()
