# Interfejsy i role — wytyczne produktowe (CONTEXT)

## Scanner UI

Android, niewielki ekran, jak najmniej tekstu, duże przyciski, czytelne komunikaty i kontekst po skanie maszyny. Celem jest skrócenie ścieżek, nie odwzorowanie rozbudowanego panelu administracyjnego. Wcześniejsze dyskusje identyfikowały akcje: wybór/odczyt kontekstu po skanie, pobranie maszyny, pobranie części, odstawienie (Putaway), relokacja, zgłoszenie problemu, inbound, outbound oraz start/pauza/zakończenie pomiaru czasu.

## Web UI

Kierownik zarządza ludźmi, zadaniami, kolejkami zleceń, wyjątkami i raportami. Pracownik może używać weba do przeglądania i zarządzania własnymi zleceniami; dostępne są również tablety. Manager wykonuje podstawowe akcje pracownika, ale autoryzacja opiera się na konfigurowalnych permissions.

## Role i przykładowe akcje

**Worker:** Scan/View Context, Pick Machine, Pick Parts, Move Machine, Report Issue, Putaway, Inbound, Outbound, Start/Pause/Complete Work.

**Manager:** powyższe plus Create Orders, Create Planning, Manage Workers/Qualifications, przegląd dashboardów, Block/Release Machine zgodnie z permissions, obsługa wyjątków.

To **katalog koncepcyjny**; nie jest równoznaczny z kompletnym zestawem endpointów ani z gotowymi przypadkami użycia bieżącego MVP. Makiety i szczegółowa nawigacja nie zostały ostatecznie zatwierdzone.
