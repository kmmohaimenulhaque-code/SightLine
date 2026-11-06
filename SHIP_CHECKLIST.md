# Ship checklist — security and privacy

None of this applies yet: SIGHTLINE has no server, database, accounts or payments today. Each item becomes a release
blocker the day that part exists. Tick it before shipping.

Legal points are a working summary for DPDP (India), GDPR (EU/UK) and CCPA/CPRA (California), not legal advice.
Status: UNVERIFIED against primary sources — have counsel confirm before a public launch.

## 1. Security locks

- [ ] **Keys on the server.** No API key, secret or token in the app, the repo or client code; only the server holds them.
- [ ] **RLS on.** Row-level security enabled on every database table.
- [ ] **Check who owns each record.** Every read, update and delete verifies the requesting user owns the record.
- [ ] **Admin behind login.** Admin pages and endpoints require an authenticated admin, checked on the server.
- [ ] **Limits on signup.** Rate limits and bot protection on signup, login and other public endpoints.
- [ ] **Webhooks verified.** Every incoming webhook (payments and others) has its signature checked before it is trusted.

## 2. Privacy compliance (DPDP + GDPR + CCPA)

- [ ] **Consent and notice.** Clear privacy policy: what is collected, why, how long it is kept, who receives it.
  Explicit opt-in where consent is the basis. No pre-ticked boxes, no dark patterns. Withdrawing consent is as easy as
  giving it.
- [ ] **Data minimisation.** Collect only what the stated purpose needs; no reuse for a new purpose without a new basis.
- [ ] **Access control.** Server-side authorisation on every request, no IDOR, role-based access, audit logs of who
  read or changed personal data.
- [ ] **User rights.** Delete account, export data, correct data, opt out of sale/sharing. Target 30 days for every
  request. Legal ceilings differ: GDPR one month (extendable by two), CCPA 45 days (extendable by 45), DPDP per the
  DPDP Rules.
- [ ] **Security.** Encryption in transit (TLS) and at rest, passwords hashed with a slow hash (Argon2id/bcrypt),
  rate limiting.
- [ ] **Breach.** GDPR: notify the supervisory authority within 72 h; tell affected users without undue delay when the
  risk is high. DPDP: notify the Data Protection Board and every affected user; the DPDP Rules set a detailed report to
  the Board within 72 h. CCPA/California: notify residents in the most expedient time possible.
- [ ] **Children.** Age gate before any data is collected. Verifiable parental consent under 18 in India (DPDP);
  under 16 in the EU unless the member state set 13–15 (GDPR); under 13 in the US (COPPA). No tracking, behavioural
  monitoring or targeted ads aimed at children. CCPA: no sale/share of under-16 data without opt-in.
- [ ] **Cross-border transfer.** EU/UK data leaves only to an adequate country, under the EU-US Data Privacy Framework,
  or under SCCs with a transfer risk assessment (consent is an exception, not a routine basis). India: transfers are
  allowed except to countries the government restricts.

## 3. Also required (missed above)

- [ ] **Lawful basis per purpose** (GDPR): written down for every processing purpose.
- [ ] **Data map and records of processing** (GDPR Art. 30): what, where, why, retention, recipients.
- [ ] **Retention schedule** with automatic deletion, including backups and logs.
- [ ] **Processor contracts (DPAs)** with every vendor and SDK that touches personal data; a public sub-processor list.
- [ ] **Third-party SDK audit.** Analytics, crash and ad SDKs disclosed and consented; nothing loads before consent.
- [ ] **Cookie/tracking consent** on the website (ePrivacy).
- [ ] **CCPA notices.** Notice at collection, "Do Not Sell or Share" link, honour Global Privacy Control, "Limit the
  Use of My Sensitive Personal Information" if sensitive data is used. Check whether the CCPA thresholds apply.
- [ ] **Contacts.** Grievance officer / contact for DPDP; DPO where GDPR requires one; EU and UK representatives if
  there is no establishment there.
- [ ] **DPIA** before launch for high-risk processing (camera video, sensors, any eye tracking or biometrics).
- [ ] **Special-category data.** Biometrics, health or face data need explicit consent and a DPIA; avoid unless needed.
- [ ] **Consent records.** Store who consented to what, when, and to which policy version.
- [ ] **Incident response plan.** Named owner, breach log, tested before launch.
- [ ] **Privacy by default.** Most protective settings on by default.
- [ ] **No personal data in logs, crash reports or analytics events.**
- [ ] **App stores.** Apple privacy nutrition label and App Tracking Transparency prompt if tracking; Google Play Data
  safety form; account deletion inside the app (Apple) plus a web deletion link (Google Play).

## 4. SIGHTLINE-specific

- [ ] **Camera and video.** Process on device where possible; upload only with explicit consent; say whether
  bystanders or faces can appear and how they are handled.
- [ ] **Sensors.** Gyroscope, IMU and BLE trigger logs are personal data once tied to a user; same rules as above.
- [ ] **Front camera / eye tracking** (research item D-011): treat as biometric data — separate opt-in and a DPIA.
- [ ] **Research and ML datasets.** Captures used for training need consent for that purpose; pseudonymise them and
  keep the provenance manifests free of names and device IDs.
