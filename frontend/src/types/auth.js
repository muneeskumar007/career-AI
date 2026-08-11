/**
 * Plain JS has no compiled types, but these JSDoc typedefs still give
 * editor autocomplete/hover info for the shapes used across the app —
 * kept here (rather than TypeScript) per the project's requested
 * frontend/src/types/ folder.
 *
 * @typedef {"candidate" | "recruiter" | "admin"} UserRole
 *
 * @typedef {Object} User
 * @property {string} id
 * @property {string} name
 * @property {string} email
 * @property {UserRole} role
 * @property {boolean} is_active
 * @property {boolean} is_verified
 * @property {string|null} phone
 * @property {string|null} avatar_url
 * @property {string} created_at
 * @property {string|null} last_login_at
 *
 * @typedef {Object} LoginPayload
 * @property {string} email
 * @property {string} password
 *
 * @typedef {Object} RegisterPayload
 * @property {string} name
 * @property {string} email
 * @property {string} password
 *
 * @typedef {Object} TokenResponse
 * @property {string} access_token
 * @property {string} token_type
 * @property {number} expires_in
 */

export {};
