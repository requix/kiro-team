'use strict';

const assert = require('node:assert');
const test = require('node:test');
const greet = require('./greet');

test('returns a greeting for a given name', () => {
  assert.strictEqual(greet('World'), 'Hello, World!');
});

test('interpolates the provided name', () => {
  assert.strictEqual(greet('Ada'), 'Hello, Ada!');
});

test('handles an empty string', () => {
  assert.strictEqual(greet(''), 'Hello, !');
});

test('throws a TypeError for non-string input', () => {
  assert.throws(() => greet(42), TypeError);
  assert.throws(() => greet(null), TypeError);
  assert.throws(() => greet(undefined), TypeError);
});
