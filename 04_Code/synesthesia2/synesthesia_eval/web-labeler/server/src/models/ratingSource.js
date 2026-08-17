/**
 * Single source of truth for classifying a row in `labels` as human vs model output.
 *
 * Three kinds of row live in that table, and only two columns distinguish them:
 *   registered human  user_id NOT NULL
 *   anonymous human   user_id NULL, labeler 'anon_<ms>_<rand>'  (POST /api/labels/anonymous)
 *   model / auto      user_id NULL, labeler e.g. 'gemini-2.0-flash'
 *
 * Classifying on user_id alone therefore lumps anonymous humans in with the model.
 * That bug made /api/stats report labeled_human = 0 while 700 real anonymous ratings
 * sat in the table, and it made Label.exportJson() drop those ratings into the
 * clip-keyed auto dict, overwriting every Gemini label in the export.
 *
 * Lives in its own module (rather than on Label) so route code can import the
 * predicates without depending on the model — `jest.mock('../models/label')`
 * auto-mocks would otherwise interpolate `undefined` into live SQL.
 */
const ANON_PREFIX = 'anon_';

const isAnonLabeler = (labeler) =>
  typeof labeler === 'string' && labeler.startsWith(ANON_PREFIX);

// `labeler` is VARCHAR(64) NOT NULL (migrate/001_create_tables.sql), so the
// NOT LIKE branch has no NULL hole to fall through.
const REGISTERED_SQL = '(user_id IS NOT NULL)';
const ANON_SQL = `(user_id IS NULL AND labeler LIKE '${ANON_PREFIX}%')`;
const HUMAN_LABEL_SQL = `(user_id IS NOT NULL OR labeler LIKE '${ANON_PREFIX}%')`;
const AUTO_LABEL_SQL = `(user_id IS NULL AND labeler NOT LIKE '${ANON_PREFIX}%')`;

module.exports = {
  ANON_PREFIX,
  isAnonLabeler,
  REGISTERED_SQL,
  ANON_SQL,
  HUMAN_LABEL_SQL,
  AUTO_LABEL_SQL,
};
