# Interfaccia moderna e versione Mac — design

Data: 2026-11-16 · Versione di arrivo: 1.1.0

## Perché
L'interfaccia attuale (Tk di serie) sembra vecchia. L'utente vuole un aspetto moderno,
scuro, con un accento chiaro "bianco non pieno". (Il glow è stato valutato e scartato.) Vuole anche una versione
per Mac nella stessa release, con istruzioni nel README per quando macOS la blocca.

## Obiettivi
- Tema scuro con accento bianco caldo (non bianco puro).
- Trascinamento dei file `.step/.stp` (e cartelle) **dentro** la finestra.
- Lista file con stato per ogni file: In attesa / In corso / ✓ Fatto / Errore.
- Avanzamento reale "N di M" invece della barra che scorre avanti e indietro.
- App per Mac Apple Silicon (`STEP2GLB.app`) nella release, accanto allo zip Windows.
- README: sezione Mac con cosa fare se macOS blocca l'app.

## Non obiettivi
- Mac Intel, firma o notarizzazione Apple, firma Windows.
- Cambiare il convertitore o le opzioni di conversione.
- Tema chiaro (l'app è solo scura).

## Anti-obiettivi
- Zip molto più pesante (niente Qt).
- Effetti glow o decorazioni pesanti: sobrio e pulito.

## Approcci considerati
- **A. Tk con stile moderno e trascinamento — scelto dall'utente.** Cambiamento contenuto,
  zip quasi invariato.
- B. CustomTkinter: aspetto più "app", ma riscrittura completa e trascinamento meno affidabile.
- C. Qt / PySide6: il più professionale, ma +60–100 MB e riscrittura totale. Scartato perché troppo.

## Design

### Aspetto (scelta mia, da confermare)
- Palette: sfondo `#0F1115`, superfici `#171A21`, bordi `#262B36`, testo `#E6E8EC`,
  testo secondario `#8B93A1`, accento `#ECE9E2` (bianco caldo al ~90%),
  successo `#7FD49B`, errore `#FF7A7A`.
- Niente tema sv-ttk: ha l'accento blu incorporato e non si adatta alla palette. Si usa il
  tema `clam` di ttk ricolorato, con il pulsante principale pieno nel colore
  dell'accento e testo scuro.
- Font: Segoe UI su Windows, font di sistema su Mac.

### Finestra
```
┌ STEP to GLB 1.1.0 ──────────────────────┐
│ ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐ │
│   Trascina qui i file .step / .stp      │
│ │  [Aggiungi file]  [Aggiungi cartella] │ │
│ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘ │
│  motore.step        12 MB   ✓ Fatto     │
│  telaio.stp         85 MB   ⟳ In corso  │
│  vite.step         0.2 MB   In attesa   │
│                      [Rimuovi] [Svuota] │
│ Qualità [Normale ▾]                     │
│ Salva   ◉ accanto ai file STEP  ○ In…   │
│ ▓▓▓▓▓▓▓░░░░ 2 di 3       ( Converti )   │
│ ▸ Dettagli (registro, chiuso di default)│
└─────────────────────────────────────────┘
```
- La lista è un `ttk.Treeview` con le colonne nome, dimensione e stato. Il percorso completo
  si vede nel tooltip o nella riga selezionata.
- Il registro testuale resta, ma in un pannello "Dettagli" che si apre e si chiude.
- Le scritte dell'interfaccia restano in inglese, come oggi.

### Trascinamento
- Dentro la finestra: libreria `tkinterdnd2` (ha binari per Windows x64 e macOS arm64).
  Se non si carica, l'app funziona lo stesso senza trascinamento.
- Sull'icona: Windows come oggi (argomenti dell'exe). Mac: gestore Tk `::tk::mac::OpenDocument`.

### Mac
- Job GitHub Actions su `macos-latest` (Apple Silicon). PyInstaller crea `STEP2GLB.app`
  (`BUNDLE`); dentro `Contents/MacOS/` ci sono sia l'app sia `step2glb-cli`.
- Smoke test: conversione del campione con `step2glb-cli`.
- Lo zip `STEP2GLB-macos-arm64.zip` si crea con `ditto -c -k --keepParent`.
- Release: i due job di build caricano gli artifact; un terzo job, solo sui tag `v*`,
  li scarica e crea la release con entrambi gli zip.

### README, sezione Mac
- Solo Mac con chip Apple (M1 o successivi).
- L'app non è firmata da Apple. Se macOS dice che non può essere aperta:
  1. macOS 15 Sequoia e successivi: prova ad aprirla, poi *Impostazioni di Sistema →
     Privacy e sicurezza → Apri comunque*, e conferma.
  2. macOS 14 e precedenti: clic destro sull'app → *Apri* → *Apri*.
  3. In alternativa, dal Terminale: `xattr -dr com.apple.quarantine /percorso/STEP2GLB.app`.

## Lasciato a chi costruisce
- Valori esatti di spaziature.
- Come il worker comunica lo stato di ogni file alla lista (la coda di messaggi c'è già).
