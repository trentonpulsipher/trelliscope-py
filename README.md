# Trelliscope
This repository contains an experimental Python port of the trelliscope R package. It is currently under heavy development.

## Quick Start

Install from source (see [Getting Started for Development](development.md)), then try the minimal example below.

Panels made from Plotly figures need the `plotly` extra, which adds kaleido for image export:

```
pip install -e ".[plotly]"
```

matplotlib panels and panels from existing image files need no extra.

### Plotly figures

```python
import pandas as pd
import plotly.express as px
from trelliscope import Trelliscope

# One summary row per iris species, plus a per-species scatter plot
iris = px.data.iris()

rows = []
for species, group in iris.groupby("species"):
    fig = px.scatter(
        group, x="sepal_width", y="sepal_length",
        title=f"Species: {species}",
    )
    rows.append({
        "species": species,
        "n": len(group),
        "mean_sepal_length": group["sepal_length"].mean(),
        "panel": fig,
    })

df = pd.DataFrame(rows)

(
    Trelliscope(df, name="Iris Species", path="./iris_display")
    .set_var_labels(
        species="Species",
        n="Count",
        mean_sepal_length="Mean Sepal Length (cm)",
    )
    .set_default_layout(ncol=3)
    .write_display()
    .view_trelliscope()
)
```

### Lazy panels (generate figures at write time)

Use `LazyPanel` when you want to generate each figure from a row of the summary
data frame rather than pre-computing all figures up front.  The function
receives a `pd.Series` (one row) and must return a Plotly or matplotlib figure.

```python
import pandas as pd
import plotly.express as px
from trelliscope import LazyPanel, Trelliscope

iris = px.data.iris()
summary = (
    iris.groupby("species")
    .agg(n=("sepal_length", "count"), mean_sl=("sepal_length", "mean"))
    .reset_index()
)

# Keep the raw data accessible in the closure
def make_panel(row):
    species_data = iris[iris["species"] == row["species"]]
    return px.scatter(species_data, x="sepal_width", y="sepal_length",
                      title=row["species"])

(
    Trelliscope(summary, name="Iris Lazy", path="./iris_lazy")
    .add_panel(LazyPanel("panel", fn=make_panel))
    .write_display()
)
```

### matplotlib figures

`Trelliscope` also accepts `matplotlib.figure.Figure` objects in panel columns
(or returned from a `LazyPanel` function).

```python
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px  # for the iris dataset only
from trelliscope import Trelliscope

iris = px.data.iris()

rows = []
for species, group in iris.groupby("species"):
    fig, ax = plt.subplots()
    ax.scatter(group["sepal_width"], group["sepal_length"])
    ax.set_title(species)
    rows.append({"species": species, "panel": fig})
    plt.close(fig)

df = pd.DataFrame(rows)
Trelliscope(df, name="Iris matplotlib", path="./iris_mpl").write_display()
```

### Interactive Plotly panels

Set the panel format to `html` to keep Plotly figures interactive (hover, zoom, pan).
html panels need no kaleido or Chrome, so they also work where static image export
cannot, such as Hex.

```python
from trelliscope.panels import PanelOptions

(
    Trelliscope(df, name="Iris Interactive", path="./iris_html")
    .set_panel_options({"panel": PanelOptions(format="html")})
    .write_display()
)
```

For a `LazyPanel`, pass `extension="html"`.
Each panel loads plotly.js from its CDN.
Small panels leave little room for axis titles, so remove them
(`fig.update_xaxes(title=None)`) when you show many columns.

## Viewing and sharing

In a notebook (Jupyter, VS Code, SageMaker, Hex), `view_trelliscope()` shows the
display in the cell output.
It needs no web server, because the data and panel images are inlined.
In a script, it opens `index.html` in your browser.

`to_html()` returns the same self-contained page as a string.
Save it to share the display as one file:

```python
from pathlib import Path

tr = Trelliscope(df, name="Iris", path="./iris_display").write_display()
Path("iris.html").write_text(tr.to_html())
```

The page loads the Trelliscope JavaScript library from unpkg, so the viewer needs
internet access.
Every panel image is inside the file, so keep panels small when a display has many
rows.

## More Examples

For a fuller walkthrough see the
[Python Trelliscope Introduction](trelliscope/examples/introduction.ipynb)
Jupyter notebook.

## Getting Started For Development
If you are interested in working on development of the Trelliscope library itself, see: [Getting Started for Development](development.md)
