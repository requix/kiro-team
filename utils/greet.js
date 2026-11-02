'use strict';

/**
 * Build a greeting for the given name.
 *
 * @param {string} name - The name to greet.
 * @returns {string} A greeting in the form 'Hello, {name}!'.
 * @throws {TypeError} If name is not a string.
 */
function greet(name) {
  if (typeof name !== 'string') {
    throw new TypeError('name must be a string');
  }
  return `Hello, ${name}!`;
}

module.exports = greet;
module.exports.greet = greet;
