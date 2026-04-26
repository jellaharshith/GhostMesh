"""Public-source event ingestion adapters.

Live event sources:    GDELT 2.0, LiveUAMap, UCDP GED.
Historical baseline:   Global Terrorism Database (GTD).
Geospatial enrichment: Overpass / OpenStreetMap, OpenTopography (SRTM DEMs).

The legacy ACLED adapter is retained on disk for back-compat only and is no
longer wired into the seeding hot path.
"""
