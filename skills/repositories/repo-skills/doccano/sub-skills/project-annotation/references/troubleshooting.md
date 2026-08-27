# Project annotation troubleshooting

## Permission problems

- **Cannot create a project**: the user must be a staff user for project creation in the documented API workflow.
- **Cannot add members**: only the project admin can manage members.
- **Cannot create labels**: confirm the label workflow is using the right project role and that `allow_member_to_create_label_type` is set when members should be allowed to add labels.
- **Cannot read or annotate examples**: confirm the user belongs to the project and has the expected role.

## Member and role problems

- **Duplicate member assignment**: a user can only be assigned once per project.
- **Role update blocked**: the project must keep at least one admin. Do not demote or remove the only admin.
- **Unexpected member visibility**: if a user was removed from the project, progress and distributions should no longer count that user.

## Annotation validation problems

- **Overlapping span rejected**: check the project's `allow_overlapping` setting.
- **Collaborative span conflict**: collaborative annotation changes whether different users can annotate the same span.
- **Category conflict rejected**: single-class classification disallows extra categories on the same example.
- **Bounding box validation failure**: `x`, `y`, `width`, and `height` must be non-negative.
- **Relation validation failure**: the relation and both spans must refer to the same example.
- **Text label uniqueness failure**: the same text label cannot be duplicated for the same example and user.

## Example, comment, and clone problems

- **Comment edit/delete permission error**: ownership rules still matter even inside the project.
- **Clone does not look right**: confirm the original project has the labels, tags, examples, and role mappings you expected before cloning.
- **Progress counters look wrong**: make sure the example state has been confirmed by the correct user and that collaborative mode is configured as intended.
