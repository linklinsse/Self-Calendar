/**
 * config.test.js — backend URL normalisation.
 *
 * normaliseApiBaseUrl is the validation boundary for a value the user types
 * and the app then interpolates into every fetch() it makes. The
 * scheme-rejection cases below are the security-relevant ones: without them
 * a settings field accepts `javascript:` and becomes a script-execution
 * vector for anyone who can talk a user into pasting one in.
 */

import { describe, expect, it } from 'vitest';
import { normaliseApiBaseUrl } from './config.js';

describe('normaliseApiBaseUrl — accepts', () => {
  it('a plain https origin', () => {
    expect(normaliseApiBaseUrl('https://calendar.example.com'))
      .toBe('https://calendar.example.com');
  });

  it('http, for self-hosted boxes on a LAN', () => {
    expect(normaliseApiBaseUrl('http://192.168.1.10:8787'))
      .toBe('http://192.168.1.10:8787');
  });

  it('a bare host:port, which is the natural thing to type', () => {
    expect(normaliseApiBaseUrl('192.168.1.10:8787'))
      .toBe('http://192.168.1.10:8787');
  });

  it('a bare hostname', () => {
    expect(normaliseApiBaseUrl('calendar.example.com'))
      .toBe('http://calendar.example.com');
  });

  it('a sub-path, for deployments that mount the API under one', () => {
    expect(normaliseApiBaseUrl('https://example.com/api'))
      .toBe('https://example.com/api');
  });
});

describe('normaliseApiBaseUrl — normalises', () => {
  it('strips a trailing slash so callers can concatenate /paths', () => {
    expect(normaliseApiBaseUrl('https://example.com/'))
      .toBe('https://example.com');
  });

  it('strips several trailing slashes', () => {
    expect(normaliseApiBaseUrl('https://example.com/api///'))
      .toBe('https://example.com/api');
  });

  it('trims surrounding whitespace, which paste routinely adds', () => {
    expect(normaliseApiBaseUrl('  https://example.com  '))
      .toBe('https://example.com');
  });

  it('drops query strings and fragments', () => {
    expect(normaliseApiBaseUrl('https://example.com/api?x=1#frag'))
      .toBe('https://example.com/api');
  });
});

describe('normaliseApiBaseUrl — rejects', () => {
  it.each([
    ['javascript:alert(1)'],
    ['data:text/html,<script>alert(1)</script>'],
    ['file:///etc/passwd'],
    ['ftp://example.com'],
  ])('the non-http(s) scheme %s', (input) => {
    expect(normaliseApiBaseUrl(input)).toBeNull();
  });

  it.each([
    [''],
    ['   '],
    [null],
    [undefined],
  ])('the empty value %p', (input) => {
    expect(normaliseApiBaseUrl(input)).toBeNull();
  });

  it('a value that parses as neither a URL nor a host', () => {
    expect(normaliseApiBaseUrl('http://')).toBeNull();
  });
});
