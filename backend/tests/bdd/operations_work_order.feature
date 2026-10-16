@mvp @work_execution @operations
Feature: Zlecenie OPERATIONS i podoperacje

  Scenario: StartOperation wymaga jawnego StartWorkOrder
    Given istnieje OPERATIONS WorkOrder WAITING z Operation WAITING
    When pracownik próbuje rozpocząć Operation
    Then operacja jest odrzucona jako INVALID_STATUS

  Scenario: Zakończenie Operation nie kończy rodzica
    Given istnieje OPERATIONS WorkOrder IN_PROGRESS z Operation IN_PROGRESS
    And aktor ma uprawnienie COMPLETE_WORK
    When aktor kończy Operation
    Then Operation ma status COMPLETED
    And WorkOrder pozostaje IN_PROGRESS

  Scenario: Pauza rodzica obejmuje tylko aktywne podoperacje
    Given WorkOrder OPERATIONS ma status IN_PROGRESS
    And pierwsza Operation jest IN_PROGRESS
    And druga Operation jest WAITING
    And trzecia Operation jest COMPLETED
    When aktor pauzuje WorkOrder
    Then WorkOrder jest PAUSED
    And pierwsza Operation jest PAUSED
    And druga Operation jest WAITING
    And trzecia Operation jest COMPLETED
    And wszystkie interwały powiązane z WorkOrder są zamknięte

  Scenario: Wznowienie rodzica nie wznawia dzieci
    Given WorkOrder OPERATIONS jest PAUSED
    And Operation jest PAUSED
    When aktor wznawia WorkOrder
    Then WorkOrder jest IN_PROGRESS
    And Operation pozostaje PAUSED

  Scenario: Dwóch pracowników może jednocześnie wykonywać jedną Operation
    Given WorkOrder OPERATIONS jest IN_PROGRESS
    And Operation jest IN_PROGRESS
    And pierwszy i drugi pracownik nie mają otwartego WorkInterval
    When obaj pracownicy rozpoczynają pracę przy tej Operation
    Then istnieją dwa otwarte WorkIntervals dla Operation
    And każdy WorkInterval należy do innego pracownika

  Scenario: Nie można kończyć OPERATIONS bez zakończonej Operation
    Given WorkOrder OPERATIONS jest IN_PROGRESS
    And wszystkie Operation są CANCELLED
    And aktor ma uprawnienie COMPLETE_OPERATIONS_WORK_ORDER
    When aktor próbuje zakończyć WorkOrder
    Then zakończenie jest odrzucone
    And WorkOrder pozostaje IN_PROGRESS

  Scenario: Anulowanie rodzica anuluje tylko nieterminalne dzieci
    Given WorkOrder OPERATIONS jest IN_PROGRESS
    And jedna Operation jest IN_PROGRESS
    And inna Operation jest COMPLETED
    When uprawniony aktor anuluje WorkOrder
    Then WorkOrder jest CANCELLED
    And pierwsza Operation jest CANCELLED
    And druga Operation pozostaje COMPLETED
