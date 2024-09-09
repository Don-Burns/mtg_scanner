import argparse
import asyncio
import json
import logging
from collections.abc import Coroutine
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Self, TypeGuard

import aiofiles
import aiofiles.os
import aiohttp

logger = logging.getLogger(__name__)


class BulkDataType(Enum):
    ORACLE_CARDS = "oracle_cards"
    UNIQUE_ARTWORK = "unique_artwork"
    DEFAULT_CARDS = "default_cards"
    ALL_CARDS = "all_cards"
    RULINGS = "rulings"


class ImageType(Enum):
    SMALL = "small"
    NORMAL = "normal"
    LARGE = "large"
    PNG = "png"
    ART_CROP = "art_crop"
    BORDER_CROP = "border_crop"


@dataclass
class CliArgs:
    bulk_data_path: Path
    image_data_dir: Path
    bulk_data_type: BulkDataType
    image_pull_limit: int
    overwrite_existing_images: bool

    @classmethod
    def parse_args(cls) -> Self:
        parser = argparse.ArgumentParser(
            description="Pulls bulk data from Scryfall",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "--bulk_data_path",
            type=Path,
            default=Path(__file__).parent / "bulk_data" / "bulk_data.json",
            help="Path to save the bulk data file",
        )
        parser.add_argument(
            "--image_data_dir",
            type=Path,
            default=Path(__file__).parent / "image_data",
            help="Directory to save the image data",
        )
        parser.add_argument(
            "--bulk_data_type",
            type=BulkDataType,
            default=BulkDataType.UNIQUE_ARTWORK.value,
            help="Type of bulk data to pull",
        )
        parser.add_argument(
            "--overwrite_existing_images",
            type=bool,
            default=False,
            help="Overwrite existing images",
        )
        parser.add_argument(
            "--image_pull_limit",
            type=int,
            default=None,
            help="Limit on the number of images to pull",
        )

        args = parser.parse_args()

        return cls(
            bulk_data_path=args.bulk_data_path,
            image_data_dir=args.image_data_dir,
            bulk_data_type=BulkDataType(args.bulk_data_type),
            image_pull_limit=args.image_pull_limit,
            overwrite_existing_images=args.overwrite_existing_images,
        )


def _is_list_dict_str(obj: object) -> TypeGuard[list[dict[str, object]]]:
    if not isinstance(obj, list):
        return False
    for item in obj:
        if not isinstance(item, dict):
            return False
        for key, val in item.items():
            if not isinstance(key, str):
                return False
            if not isinstance(val, object):
                return False

    return True


class ScryfallApiClient:
    def __init__(self, http_session: aiohttp.ClientSession) -> None:
        self.session = http_session
        self.base_url = "https://api.scryfall.com"

    async def get_bulk_data(self, type_: BulkDataType) -> list[dict[str, object]]:
        """
        Collects the latest bulk data for the given type
        Api Docs: https://scryfall.com/docs/api/bulk-data

        Args:
            type_ (BulkDataType): type of bulk data to pull

        Returns:
            dict[str, object]: Contents of the bulk data file
        """

        logger.info("Getting latest bulk data link")
        async with self.session.get(f"{self.base_url}/bulk-data") as response:
            response.raise_for_status()
            resp_dict = await response.json()
            assert isinstance(resp_dict, dict)
            resp_data = resp_dict["data"]

            for entry in resp_data:
                if entry["type"] == type_.value:
                    bulk_data_url = entry["download_uri"]
                    break
        logger.info("Downloading bulk data")
        async with self.session.get(bulk_data_url) as response:
            response.raise_for_status()
            resp_dict = await response.json()
            assert _is_list_dict_str(resp_dict)

            return resp_dict


async def save_bulk_data(bulk_data: list[dict[str, object]], path: Path) -> None:
    logger.info("Saving bulk data to %s", path)
    await aiofiles.os.makedirs(path.parent, exist_ok=True)
    async with aiofiles.open(path, "w") as file:
        # NOTE: this json.dumps not massively efficient, may need to be changed for larger files
        string = json.dumps(bulk_data)
        await file.write(string)
    logger.info("Bulk data saved")


async def save_image_data(
    image_data: list[dict[str, object]],
    out_dir: Path,
    http_session: aiohttp.ClientSession,
    overwrite_existing: bool = False,
    limit: int | None = None,
    image_size: ImageType = ImageType.SMALL,
) -> None:

    await aiofiles.os.makedirs(out_dir, exist_ok=True)

    tasks: list[Coroutine[object, object, object]] = []
    for i, item in enumerate(image_data, 1):
        if limit is not None and i > limit:
            logger.info("Image pull limit of %d reached", i)
            break
        assert isinstance(item, dict)
        scryfall_id = item["id"]
        card_layout = item["layout"]
        assert isinstance(scryfall_id, str)
        assert isinstance(card_layout, str)
        # skip certain card layouts
        if card_layout in ("art_series",):
            continue
        # handle dual faced cards
        try:
            if "image_uris" not in item:
                image_uri = item["card_faces"][0]["image_uris"][image_size.value]  # type: ignore
            else:
                image_uri = item["image_uris"][image_size.value]  # type: ignore
        except KeyError as err:
            raise KeyError(
                f"Error getting image uri for {scryfall_id} with {card_layout=}. {item=}"
            ) from err

        assert isinstance(image_uri, str)
        img_path = out_dir / f"{scryfall_id}.jpg"
        tasks.append(
            download_and_save(http_session, image_uri, img_path, overwrite_existing)
        )

    await asyncio.gather(*tasks)


async def download_and_save(
    http_session: aiohttp.ClientSession,
    image_uri: str,
    img_path: Path,
    overwrite: bool,
) -> None:
    # if the file exists and not overwriting, skip
    if overwrite is False and await aiofiles.os.path.exists(img_path):
        logger.debug("%s already exists, skipping", img_path)
        return

    # download and write the file
    logger.debug("Downloading %s", image_uri)
    async with http_session.get(image_uri) as response:
        response.raise_for_status()
        img_bytes = response.read()
        async with aiofiles.open(img_path, "wb") as f:
            await f.write(await img_bytes)


async def pull_scryfall_data(
    image_data_dir: Path = Path(__file__).parent / "image_data",
    bulk_data_dir: Path = Path(__file__).parent / "bulk_data",
    overwrite_existing_images: bool = False,
    image_pull_limit: int | None = None,
) -> None:
    """
    Pulls data from scryfall and saves it to the given directories

    Args:
        image_data_dir (Path, optional): path to save scryfall card images to. Defaults to Path(__file__).parent/"image_data".
        bulk_data_dir (Path, optional): path to save bulk card data to. Defaults to Path(__file__).parent/"bulk_data".
        overwrite_existing_images (bool, optional): Whether to overwrite any existing images for cards already pulled. Defaults to False.
        image_pull_limit (int | None, optional): Max number of images to pull, `None`=`No Limit`. Defaults to None.
    """
    tasks: list[Coroutine[object, object, object]] = []
    # NOTE: certain headers are required by scryfall: https://scryfall.com/docs/api
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "mtg_scanner",
            "Accept": "*/*",
        }
    ) as session:
        client = ScryfallApiClient(session)
        bulk_data = await client.get_bulk_data(BulkDataType.UNIQUE_ARTWORK)
        tasks.append(save_bulk_data(bulk_data, bulk_data_dir))

        tasks.append(
            save_image_data(
                bulk_data,
                image_data_dir,
                session,
                overwrite_existing_images,
                image_pull_limit,
            )
        )

        await asyncio.gather(*tasks)


async def main() -> int:
    """
    Main function
    """

    args = CliArgs.parse_args()
    logger.info("Args: %s", args)

    await pull_scryfall_data(
        image_data_dir=args.image_data_dir,
        bulk_data_dir=args.bulk_data_path,
        overwrite_existing_images=args.overwrite_existing_images,
        image_pull_limit=args.image_pull_limit,
    )

    logger.info("Finished")

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(asyncio.run(main()))
