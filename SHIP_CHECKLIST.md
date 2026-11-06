# Ship checklist — security and privacy

None of this applies yet: SIGHTLINE has no server, database, accounts or payments today. Each item becomes a release
blocker the day that part exists. Tick it before shipping.

Approach: one global baseline built to the strictest common rule, so the same product is sound in every market, plus
the few local rules that go further. Covers GDPR/UK GDPR, US federal and state laws (CCPA/CPRA and others, COPPA,
BIPA), Brazil LGPD, Canada PIPEDA, Australia, Japan APPI, South Korea PIPA and China PIPL.
Not legal advice. Status: UNVERIFIED against primary sources — have counsel confirm before a public launch.

## 1. Security locks

- [ ] **Keys on the server.** No API key, secret or token in the app, the repo or client code; only the server holds them.
- [ ] **RLS on.** Row-level security enabled on every database table.
- [ ] **Check who owns each record.** Every read, update and delete verifies the requesting user owns the record.
- [ ] **Admin behind login.** Admin pages and endpoints require an authenticated admin, checked on the server.
- [ ] **Limits on signup.** Rate limits and bot protection on signup, login and other public endpoints.
- [ ] **Webhooks verified.** Every incoming webhook (payments and others) has its signature checked before it is trusted.

## 2. Global privacy baseline

- [ ] **Consent and notice.** Clear privacy policy: what is collected, why, legal basis, how long it is kept, who
  receives it, which countries it goes to. Explicit opt-in where consent is the basis; no pre-ticked boxes, no dark
  patterns. Withdrawing consent is as easy as giving it.
- [ ] **Data minimisation.** Collect only what the stated purpose needs; no reuse for a new purpose without a new basis.
- [ ] **Access control.** Server-side authorisation on every request, no IDOR, role-based access, audit logs of who
  read or changed personal data.
- [ ] **User rights.** Access/export, correct, delete account, object, opt out of sale, sharing, targeted ads and
  profiling. Verify identity before acting. Answer within 15 days (meets Brazil, the shortest common deadline; GDPR
  allows one month, US state laws 45 days).
- [ ] **Security.** Encryption in transit (TLS) and at rest, passwords hashed with a slow hash (Argon2id/bcrypt),
  rate limiting, MFA for staff and admin accounts.
- [ ] **Breach.** Notify regulators within 72 h of discovery as the default (GDPR, South Korea), sooner where required
  (Brazil: 3 working days; China: immediately). Tell affected users without undue delay when they are at risk.
- [ ] **Children.** Age gate before any data is collected. Parental consent below the local digital age of consent
  (13 in the US, 13–16 across the EU); child-protective defaults and no profiling, tracking or targeted ads for anyone
  under 18 (UK Age Appropriate Design Code standard). Simplest global option: 18+ only, or a youth mode with these
  defaults built in.
- [ ] **Cross-border transfer.** Map where data is stored and processed. Move personal data out of a country only under
  that country's mechanism: EU/UK adequacy, the EU-US Data Privacy Framework, SCCs (EU) or the IDTA/Addendum (UK),
  with a transfer risk assessment. Consent is an exception, not the routine basis. China and Russia have localisation
  or approval rules: check before launching there.

## 3. Also required

- [ ] **Lawful basis per purpose**, written down for every processing purpose.
- [ ] **Data map and records of processing**: what, where, why, retention, recipients, transfers.
- [ ] **Retention schedule** with automatic deletion, including backups and logs.
- [ ] **Processor contracts (DPAs)** with every vendor and SDK that touches personal data; a public sub-processor list.
- [ ] **Third-party SDK audit.** Analytics, crash and ad SDKs disclosed and consented; nothing loads before consent.
- [ ] **Cookie/tracking consent** on the website, opt-in for non-essential cookies (EU/UK standard).
- [ ] **US opt-outs.** "Do Not Sell or Share" link, honour Global Privacy Control and other universal opt-out signals,
  "Limit the Use of My Sensitive Personal Information" (California); opt-in for sensitive data in the states that
  require it. Check which state-law thresholds apply.
- [ ] **Biometrics.** Written consent and a published retention policy before collecting any face, eye or other
  biometric data (Illinois BIPA, with private lawsuits; GDPR special category). Avoid unless needed.
- [ ] **Contacts.** Privacy contact on the website; DPO where GDPR requires one; EU and UK representatives if there is
  no establishment there; local representatives where Brazil, China or Korea require them.
- [ ] **DPIA** before launch for high-risk processing (camera video, sensors, eye tracking, children, biometrics).
- [ ] **Consent records.** Store who consented to what, when, and to which policy version.
- [ ] **Incident response plan.** Named owner, breach log, regulator contact list per country, tested before launch.
- [ ] **Privacy by default.** Most protective settings on by default.
- [ ] **No personal data in logs, crash reports or analytics events.**
- [ ] **App stores.** Apple privacy nutrition label and App Tracking Transparency prompt if tracking; Google Play Data
  safety form; account deletion inside the app (Apple) plus a web deletion link (Google Play).

## 4. SIGHTLINE-specific

- [ ] **Camera and video.** Process on device where possible; upload only with explicit consent; say whether
  bystanders or faces can appear and how they are handled.
- [ ] **Sensors.** Gyroscope, IMU and BLE trigger logs are personal data once tied to a user; same rules as above.
- [ ] **Front camera / eye tracking** (research item D-011): treat as biometric data — separate written opt-in,
  retention policy and a DPIA.
- [ ] **Research and ML datasets.** Captures used for training need consent for that purpose; pseudonymise them and
  keep the provenance manifests free of names and device IDs.
