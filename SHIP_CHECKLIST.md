# Ship checklist — security locks

None of these apply yet: SIGHTLINE has no server, database, accounts or payments today. Each one becomes a release
blocker the day that part exists. Tick it before shipping.

- [ ] **Keys on the server.** No API key, secret or token in the app, the repo or client code; only the server holds them.
- [ ] **RLS on.** Row-level security enabled on every database table.
- [ ] **Check who owns each record.** Every read, update and delete verifies the requesting user owns the record.
- [ ] **Admin behind login.** Admin pages and endpoints require an authenticated admin, checked on the server.
- [ ] **Limits on signup.** Rate limits and bot protection on signup, login and other public endpoints.
- [ ] **Webhooks verified.** Every incoming webhook (payments and others) has its signature checked before it is trusted.
