import test from 'node:test';
import assert from 'node:assert/strict';

import { buildUserPayload } from './formPayloads.js';

test('buildUserPayload includes status for create and update requests', () => {
  const payload = buildUserPayload(
    {
      username: 'demo',
      password: 'secret',
      status: 'blocked',
    },
    { requirePassword: true }
  );

  assert.equal(payload.status, 'blocked');
});
