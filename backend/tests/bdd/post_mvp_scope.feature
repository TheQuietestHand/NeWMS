@post_mvp
Feature: Przyszłe reguły nieobjęte aktualnym MVP
  Plik opisuje kierunek wymagań; szczegóły pozostają otwarte i nie stanowią kontraktu implementacyjnego.

  @pending_design
  Scenario: Autoryzowana naprawa przy utrzymanej blokadzie
    Given maszyna jest zablokowana
    When uprawniona osoba wykonuje przewidzianą procedurę naprawczą
    Then blokada pozostaje aktywna do osobnego zwolnienia

  @pending_design
  Scenario: Weryfikacja kwalifikacji dla modelu maszyny
    Given pracownik nie ma wymaganej kwalifikacji dla danego modelu
    When próbuje rozpocząć pracę wymagającą tej kwalifikacji
    Then docelowa polityka kwalifikacji rozstrzyga dostęp
