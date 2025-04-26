import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import seaborn as sns
import plotly.express as px
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt

# Pfade
CSV_PATH = "BITTE ANPASSEN AN LOKALE DATEI"
SHAPEFILE_PATH = "BITTE ANPASSEN AN LOKALE DATEI"

# CSV mit Koordinaten laden
df = pd.read_csv(CSV_PATH)
print(df.columns)

#Wandelt Startorte in GeoPoints um --> für räumliche Verarbeitung
gdf_start = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.Start_Lon, df.Start_Lat),
    crs="EPSG:4326")

#Shapefile mit Stadtteilgrenzen wird geladen und bringt diese in WGS84
# (EPSG:4326) um mit den Koordinaten der Startorte zu arbeiten
gdf_districts = gpd.read_file(SHAPEFILE_PATH)
gdf_districts = gdf_districts.to_crs(epsg=4326)

#OPTIONAL: Überblick über Spalten
print(gdf_districts.columns)

#Spalte mit Stadtteilnamen
district_col = "NAME"

#Spatial Join: Ermittlung welcher Stadtteil zu welchem Punkt gehört
#Startorte
gdf_joined = gpd.sjoin(gdf_start, gdf_districts[[district_col, "geometry"]], how="left", predicate="within")
gdf_joined = gdf_joined.rename(columns={district_col: "Start_Stadtteil"})

#Zielorte
gdf_ziel = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.Ziel_Lon, df.Ziel_Lat),
    crs="EPSG:4326"
)
gdf_joined_ziel = gpd.sjoin(gdf_ziel, gdf_districts[[district_col, "geometry"]], how="left", predicate="within")
gdf_joined["Ziel_Stadtteil"] = gdf_joined_ziel[district_col]

#Ergebnisse werden gespeichert
gdf_joined.drop(columns="geometry", inplace=True)
gdf_joined.to_csv("wegetagebuch_mit_stadtteilen.csv", index=False)



'''Aggregation der VERKEHRSFLÜSSE'''
#Gruppierung nach Start- und Zielstadtteil
print("Tabelle für VERKEHRSFLUESSE")
#Zählen der Anzahl der Fahrten zwischen Start- und Zielstadtteil
verkehrsfluesse = gdf_joined.groupby(["Start_Stadtteil", "Ziel_Stadtteil"]).size().reset_index(name="Anzahl_Fahrten")

#Optional sortieren
verkehrsfluesse = verkehrsfluesse.sort_values(by="Anzahl_Fahrten", ascending=False)

#Vorschau
print(verkehrsfluesse.head(10))

'''VERKEHRSMITTEL'''
#Gruppierung nach Stadtteil und Verkehrsmittel
print(" ")
print("Tabelle für VERKEHRSMITTEL")

verkehrsfluesse_modalsplit = gdf_joined.groupby(["Start_Stadtteil", "Ziel_Stadtteil", "Verkehrsmittel"]).size().reset_index(name="Anzahl")
print(verkehrsfluesse_modalsplit.head(10))

'''ZWECKE'''
#Gruppierung nach Stadtteil und Zweck
print(" ")
print("Tabelle für ZWECKE")
verkehrsfluesse_zweck = gdf_joined.groupby(["Start_Stadtteil", "Ziel_Stadtteil", "Zweck"]).size().reset_index(name="Anzahl")
print(verkehrsfluesse_zweck.head(10))



'''VISUALISIERUNG'''
#Gruppierung der Flüsse --> Erstellt eine Matrix mit Start- und Zielstadtteilen
verkehrs_matrix = gdf_joined.groupby(["Start_Stadtteil", "Ziel_Stadtteil"]).size().unstack(fill_value=0)
# Vorschau
print(verkehrs_matrix.head())

#Interaktive Heatmap mit Plotly:
verkehrs_matrix_reset = verkehrs_matrix.reset_index().melt(id_vars="Start_Stadtteil", var_name="Ziel_Stadtteil", value_name="Anzahl")
#Zeigt die Matrix als quadratische Heatmap an
fig = px.density_heatmap(
    verkehrs_matrix_reset,
    x="Ziel_Stadtteil",
    y="Start_Stadtteil",
    z="Anzahl",
    color_continuous_scale="Viridis",
    title="Verkehrsflüsse zwischen den Stadtteilen (interaktive Heatmap)")
fig.update_layout(xaxis_tickangle=-45)
fig.show()


#Top-N Verbindungen berechnen
top_n = 10
linien_df = df.groupby(
    ["Start_Lat", "Start_Lon", "Ziel_Lat", "Ziel_Lon"]
).size().reset_index(name="Anzahl")
linien_top = linien_df.sort_values(by="Anzahl", ascending=False).head(top_n)

#Heatmap-Daten vorbereiten
start_heat = df.groupby(["Start_Lat", "Start_Lon"]).size().reset_index(name="count")
ziel_heat = df.groupby(["Ziel_Lat", "Ziel_Lon"]).size().reset_index(name="count")

#Karte zentriert auf Karlsruhe erstellen
karte = folium.Map(location=[49.0069, 8.4037], zoom_start=12, tiles="cartodbpositron")

#Linien werden eingefügt
for _, row in linien_top.iterrows():
    folium.PolyLine(
        locations=[(row["Start_Lat"], row["Start_Lon"]), (row["Ziel_Lat"], row["Ziel_Lon"])],
        color="darkred",
        weight=2 + row["Anzahl"] / 10,
        opacity=0.6,
        tooltip=f"Fahrten: {row['Anzahl']}"
    ).add_to(karte)

#Heatmap für Startorte
heat_start = HeatMap(start_heat[["Start_Lat", "Start_Lon", "count"]].values.tolist(), radius=12, name="Startorte-Heatmap")
karte.add_child(heat_start)
#Heatmap für Zielorte
heat_ziel = HeatMap(ziel_heat[["Ziel_Lat", "Ziel_Lon", "count"]].values.tolist(), radius=12, name="Zielorte-Heatmap")
karte.add_child(heat_ziel)

#Layer Con
folium.LayerControl().add_to(karte)

#Karte speichern
karte.save("verkehrsfluesse_karlsruhe.html")
print("Karte erfolgreich erstellt und gespeichert unter: verkehrsfluesse_karlsruhe.html")


'''MODALSPLIT VISUALISIERUNG'''
#Gruppieren nach Relation und Verkehrsmittel
modalsplit_df = df.groupby(["Startort", "Zielort", "Verkehrsmittel"]).size().reset_index(name="Fahrten")

#Pivot-Tabelle: Relation als Index, Verkehrsmittel als Spalten
modalsplit_pivot = modalsplit_df.pivot_table(
    index=["Startort", "Zielort"],
    columns="Verkehrsmittel",
    values="Fahrten",
    fill_value=0)

#Prozentual normalisieren je Relation
modalsplit_norm = modalsplit_pivot.div(modalsplit_pivot.sum(axis=1), axis=0)

#Visualisierung: Gestapelte Balken für die Top-N Relationen
top_rels = modalsplit_pivot.sum(axis=1).sort_values(ascending=False).head(10).index
plot_df = modalsplit_norm.loc[top_rels]

#Visualisierung des gestapelten Balkendiagramms
plot_df.plot(kind="bar", stacked=True, figsize=(14, 6), colormap="tab20")
plt.title("Modalsplit der Top 10 Relationen")
plt.ylabel("Anteil der Fahrten")
plt.xlabel("Relation (Start -> Ziel)")
plt.xticks(ticks=range(len(plot_df)), labels=[f"{s} -> {z}" for s, z in plot_df.index], rotation=45, ha="right")
plt.legend(title="Verkehrsmittel", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.show()
