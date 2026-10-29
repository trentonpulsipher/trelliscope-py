"""
Contains utility functions that facilitate writing the html and support files for viewing.
"""
import base64
import json
import mimetypes
from pathlib import Path

DEFAULT_JAVASCRIPT_VERSION = "0.7.5"


def write_index_html(
    output_path: str, trelliscope_id: str, javascript_version: str = None
) -> None:
    """
    Writes the main index.html file for the Trelliscope to the output directory.

    Args:
        output_path: The absolute path to the directory that will contain
            the file.
        trelliscope_id: The ID of the Trelliscope object.
        javascript_version: The version of the Trelliscope JavaScript library
            to include from the CDN. If none is provided, the value will be
            read from the main config file.
    """

    if javascript_version is None:
        javascript_version = DEFAULT_JAVASCRIPT_VERSION

    html_content = _get_index_html_content(trelliscope_id, javascript_version)
    html_file = Path(output_path) / "index.html"

    with open(html_file, "w") as output_file:
        output_file.write(html_content)


def _get_index_html_content(trelliscope_id: str, javascript_version: str) -> str:
    """
    Gets the contents of the base index.html page.

    Args:
        trelliscope_id: The ID of the Trelliscope object.
        javascript_version: The version of the Trelliscope
            JavaScript library to include from the CDN.

    Returns:
        A string containing the html to write.
    """

    # Note that because this is a format string any literal {}'s need to be escaped by doubling
    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<script src="https://unpkg.com/trelliscopejs-lib@{javascript_version}/dist/assets/index.js"></script>
<link href="https://unpkg.com/trelliscopejs-lib@{javascript_version}/dist/assets/index.css" rel="stylesheet" />

</head>
<body onload="trelliscopeApp('{trelliscope_id}', 'config.jsonp')">
  <div id="{trelliscope_id}" class="trelliscope-spa">
</body>
</html>
"""
    return index_html_content


def get_self_contained_html(output_path: str, javascript_version: str = None) -> str:
    """
    Builds a single html page holding a written Trelliscope, with its data and
    local panel images inlined, so it displays without a web server or file
    access (for example inside Hex, SageMaker, or VS Code notebook output).

    Args:
        output_path: The directory that `write_display` wrote.
        javascript_version: The version of the Trelliscope JavaScript library
            to include from the CDN.

    Returns:
        A string containing the html.
    """
    if javascript_version is None:
        javascript_version = DEFAULT_JAVASCRIPT_VERSION

    output_dir = Path(output_path)
    config = _read_app_file(output_dir / "config")
    displays_dir = output_dir / "displays"
    display_list = _read_app_file(displays_dir / "displayList")

    displays = {}
    for display_dir in sorted(p for p in displays_dir.iterdir() if p.is_dir()):
        display_info = _read_app_file(display_dir / "displayInfo")
        meta_data_text = (display_dir / "metaData.js").read_text()
        meta_data = json.loads(meta_data_text[meta_data_text.index("=") + 1 :])

        for meta in display_info["metas"]:
            source = meta.get("source") or {}
            if meta["type"] != "panel" or not source.get("isLocal"):
                continue
            # The JS app uses a non-local panel's value as its src unchanged.
            source["isLocal"] = False
            for row in meta_data:
                if row.get(meta["varname"]):
                    row[meta["varname"]] = _to_data_uri(display_dir / row[meta["varname"]])

        displays[display_info["name"]] = {
            "displayInfo": display_info,
            "metaData": meta_data,
        }

        for entry in display_list:
            if entry["name"] == display_info["name"] and entry.get("thumbnailurl"):
                entry["thumbnailurl"] = _to_data_uri(display_dir / entry["thumbnailurl"])

    app_data = {"config": config, "displayList": display_list, "displays": displays}
    # Stop a "</script>" inside the data from closing the script element early.
    app_data_json = json.dumps(app_data).replace("</", "<\\/")
    trelliscope_id = config["id"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<script src="https://unpkg.com/trelliscopejs-lib@{javascript_version}/dist/assets/index.js"></script>
<link href="https://unpkg.com/trelliscopejs-lib@{javascript_version}/dist/assets/index.css" rel="stylesheet" />
</head>
<body style="margin: 0; height: 100vh">
  <div id="{trelliscope_id}" class="trelliscope-spa"></div>
  <script>trelliscopeApp("{trelliscope_id}", {app_data_json});</script>
</body>
</html>
"""


def _read_app_file(path_without_extension: Path):
    """Reads an app file that `write_display` wrote as either jsonp or json."""
    jsonp_file = path_without_extension.with_suffix(".jsonp")
    if jsonp_file.exists():
        text = jsonp_file.read_text()
        return json.loads(text[text.index("(") + 1 : text.rindex(")")])
    return json.loads(path_without_extension.with_suffix(".json").read_text())


def _to_data_uri(file_path: Path) -> str:
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def write_id_file(output_path: str, trelliscope_id: str) -> None:
    """
    Writes the id file that belongs in the main output directory.

    Args:
        output_path: The absolute path to the directory that will contain
            the file.
        trelliscope_id: The ID of the Trelliscope object.
    """

    id_file = Path(output_path) / "id"

    with open(id_file, "w") as output_file:
        output_file.write(trelliscope_id)
