# This module is intentionally empty.
#
# The db_session_injector decorator was removed in favour of explicit session
# injection: every service function now accepts `session: Session` as a plain
# argument, and routes supply it via the `SessionDep` FastAPI dependency.
#
# This approach gives each request a single shared session (better transaction
# semantics), keeps the dependency graph visible to FastAPI's DI system, and
# makes service functions straightforward to test without the decorator magic.
