@mvp @machine_block
Feature: Blokada maszyny i spójność zatrzymania pracy

  Scenario: BlockMachine zatrzymuje powiązaną aktywną pracę
    Given maszyna nie ma aktywnej blokady
    And powiązany DIRECT WorkOrder jest IN_PROGRESS
    When uprawniony aktor blokuje maszynę
    Then maszyna ma jedną aktywną blokadę
    And WorkOrder jest PAUSED
    And jego WorkInterval jest zamknięty z powodem MACHINE_BLOCK
    And w historii zapisany jest aktor blokady

  Scenario: Zdjęcie blokady nie wznawia pracy
    Given maszyna ma aktywną blokadę
    And powiązany WorkOrder jest PAUSED
    When uprawniony aktor zwalnia blokadę
    Then maszyna nie ma aktywnej blokady
    And WorkOrder pozostaje PAUSED
    And żaden WorkInterval nie zostaje automatycznie otwarty

  Scenario: Niezależna druga blokada jest konfliktem
    Given maszyna ma aktywną blokadę
    When aktor wysyła nowe niezależne BlockMachine
    Then operacja jest odrzucona jako CONFLICT
    And maszyna nadal ma jedną aktywną blokadę

  Scenario: Ponowienie tej samej komendy nie powiela skutku
    Given BlockMachine zakończyło się sukcesem z request_id R
    When aktor ponawia tę samą komendę z request_id R
    Then otrzymuje poprzedni rezultat
    And nie powstaje nowa blokada

  Scenario: Zakończenie pracy na zablokowanej maszynie jest zabronione
    Given maszyna ma aktywną blokadę
    And jest z nią powiązany WorkOrder
    When aktor próbuje standardowo zakończyć powiązaną pracę
    Then operacja jest odrzucona jako TARGET_BLOCKED

  Scenario: Błąd w trakcie kaskady wycofuje całą blokadę
    Given maszyna ma dwa powiązane aktywne WorkOrders
    When BlockMachine napotyka błąd podczas pauzowania drugiego zlecenia
    Then transakcja jest wycofana
    And żadna część blokady ani pauzy nie pozostaje zapisana
