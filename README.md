# Quoka Getter

Eine Home Assistant Integration, die automatisch aktuelle Inserate von [Quoka](https://www.quoka.de) zu deinen gewünschten Suchbegriffen und Kategorien sammelt und sie über eine passende Dashboard-Karte anzeigt.

## Installation

1. Füge dieses Repository in HACS als benutzerdefinierte Integration hinzu.
2. Installiere die Integration **Quoka Getter**. Die Lovelace-Ressource `quoka-card` wird automatisch mit ausgeliefert und nach dem Neustart von Home Assistant in `www/community/quoka-card` verfügbar sein.
3. Starte Home Assistant neu.

## Konfiguration

1. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen** und suche nach **Quoka Getter**.
2. Trage mindestens einen Suchbegriff ein. Mehrere Werte können mit Komma getrennt werden.
3. Optional: Gib Kategorien an, um die Ergebnisse weiter einzugrenzen.
4. Lege das Aktualisierungsintervall (in Minuten) fest.
5. Speichere den Flow, die Integration erstellt einen Sensor `sensor.quoka_listings` mit allen Ergebnissen in den Attributen.
6. Füge dem Dashboard eine benutzerdefinierte Karte hinzu und wähle `quoka-card` als Typ. Setze die Entity auf den erstellten Sensor.

## Funktionsweise

* Die Integration ruft die Quoka-Webseite zyklisch ab und sammelt die Inserate entsprechend deiner Suchbegriffe und Kategorien.
* Ergebnisse werden dedupliziert und als Attribute des Sensors bereitgestellt.
* Die Dashboard-Karte stellt Titel, Preis, Standort, Veröffentlichungsdatum und Vorschaubilder übersichtlich dar.

## Feature-Checkliste

- [x] GUI-Konfiguration mit Unterstützung für mehrere Suchbegriffe und Kategorien
- [x] Datenaktualisierung über einen DataUpdateCoordinator mit einstellbarem Intervall
- [x] Bereitstellung einer Lovelace-Karte (`quoka-card`) zur Visualisierung der Inserate
- [x] Manueller Aktualisierungs-Button inklusive Service für Sofortabfragen
- [x] Konfigurierbare Obergrenze für die Anzahl geladener Inserate
- [x] Historie behält ältere Inserate bis zur definierten Obergrenze bei
- [x] Fehlertolerante Behandlung nicht verfügbarer Suchseiten (404)
- [x] Dokumentierter Aktualisierungsdienst über `services.yaml`

## Entwicklung

```bash
python -m compileall custom_components
```

Der obenstehende Befehl dient als schneller Syntax-Check für die Python-Module der Integration.
