@mvp @work_execution @direct
Feature: Cykl życia WorkOrder w trybie DIRECT
  Scenariusze dokumentują wymagane zachowanie; definicje kroków Behave nie są częścią paczki.

  Scenario: Utworzenie DIRECT jest w stanie WAITING
    Given aktor ma uprawnienie CREATE_WORK_ORDER
    When tworzy WorkOrder w trybie DIRECT
    Then WorkOrder ma status WAITING

  Scenario: Start bez przydziału nie przypisuje wykonawcy
    Given istnieje DIRECT WorkOrder WAITING bez przypisanego pracownika i stanowiska
    And pracownik nie ma otwartego WorkInterval
    When pracownik rozpoczyna WorkOrder
    Then WorkOrder ma status IN_PROGRESS
    And WorkInterval pracownika jest otwarty
    And WorkOrder pozostaje bez przypisanego pracownika

  Scenario: Pauza i wznowienie otwierają oddzielne przedziały
    Given pracownik wykonuje DIRECT WorkOrder IN_PROGRESS
    When pracownik pauzuje WorkOrder
    And pracownik wznawia WorkOrder
    Then istnieją dwa różne WorkIntervals
    And pierwszy interwał jest zamknięty
    And drugi interwał jest otwarty

  Scenario: Zakończenie wymaga COMPLETE_WORK
    Given aktor nie posiada COMPLETE_WORK
    And istnieje DIRECT WorkOrder IN_PROGRESS
    When aktor próbuje zakończyć WorkOrder
    Then operacja jest odrzucona jako PERMISSION_DENIED
    And WorkOrder pozostaje IN_PROGRESS

  Scenario: Jeden pracownik nie może otworzyć drugiego interwału
    Given pracownik ma otwarty WorkInterval
    And istnieje inny DIRECT WorkOrder WAITING
    When ten sam pracownik próbuje rozpocząć drugi WorkOrder
    Then operacja jest odrzucona jako CONFLICT

  Scenario: Terminalne zlecenie nie może zostać wznowione
    Given DIRECT WorkOrder ma status COMPLETED
    When aktor próbuje wznowić WorkOrder
    Then operacja jest odrzucona jako INVALID_STATUS
