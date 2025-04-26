# VSM2_Info_Projekt
Dies hier ist ein Repository für das Informatikprojekt zur Analyse eines synthetischen Wegetagebuchs

Dieses Programm sollte drei verschiedene Grafiken ausgeben, eine interaktive Heatmap, eine Karte von Karlsruhe auch mit Heatpoints und dazugehörigen Linien für die Wege sowie ein gestapeltes Balkendiagramm für die Angabe von den Top 10 Wegen mit Angabe der Verkehrsmittel

Bitte laden Sie diesen Code herunter und lassen sie in ihrer lokalen Programmierumgebung laufen ändern Sie dabei bitte die Pfade für die CSV-Datei und die Shape-Datei in Zeile 11 und 12.

Fürs lokale ablaufen des Programms ist hier noch die Bash eingabe zum Herunterladen aller Bibliotheken und Erweiterungen die verwendet wurden:
pip install pandas geopandas shapely seaborn plotly.express folium matplotlib

Kurzbericht Mobilitätsprojekt:

Mobilitätsanalyse Karlsruhe – Dokumentation
Diese Analyse untersucht ein synthetisches Wegetagebuch für Karlsruhe. 
Ziel der Analyse ist es, Verkehrsflüsse zwischen den Stadtteilen zu analysieren und Handlungsempfehlungen daraus abzuleiten
1.	Geo-/Datenprozessierung
Datengrundlage: 
-	Datei: „wegetagebuch_karlsruhe_csv“ + wegetagebuchgen.py + Stadtteile_Karlsruhe.shp
-	CSV enthält: Start-/Zielorte, Koordinaten, Verkehrsmittel, Zweck, Uhrzeit, Entfernung
Stadtteil-Zuordnung
```python
gdf_start = gpd.GeoDataFrame(...)
gdf_districts = gpd.read_file(...).to_crs(epsg=4326)
gdf_joined = gpd.sjoin(...)
gdf_joined['Ziel_Stadtteil'] = ...
```
-> Die Punkte werden mit GeoPandas dem jeweiligen Stadtteil zugeordnet (sog. Spatial Join)

2.	Aggregation 
Verkehrsflüsse:
```python
Verkehrsluesse = gdf_joined.groupby(['Start_Stadtteil', 'Ziel_Stadtteil']).size()
```
-> Zählt alle Wege zwischen zwei Stadtteilen.
Verkehrsmittel & Zweck:
```python
verkehrsfluesse_modalsplit = gdf_joined.groupby([...])
verkehrsfluesse_zweck = gdf_joined.groupby([...])
```
-> Zeigt Modalsplit und Zweckverteilung pro Relation.

3.	Visualisierungen
Heatmap (interaktiv)
```python
px.density_heatmap(...)
```
Kartenvisualisierung (Folium)
```python
karte = folium.Map(...)
PolyLine(...)  # Top 10 Verbindungen
HeatMap(...)   # Start- und Zielorte
```
->	Darstellung von Verbindungsdichte und Richtung.
Modalsplit – Gestapelte Balken
```python
modalsplit_df = df.groupby([...]).size()
pivot_table → normiert → bar plot (gestapelt)
```
->	Prozentualer Anteil je Verkehrsmittel pro Verbindung.
