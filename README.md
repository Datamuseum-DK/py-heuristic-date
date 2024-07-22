# py-heuristic-date
Python function to heuristically interpret strings as dates 

It's a bit late to tell the computer-pioneers in the middle of last
century to use proper ISO-8601 format, so we have to interpret what
they wrote as best we can.

This python function does a pretty good job at the material we have
in our archives in Datamuseum.dk, by taking the same heuristic
approach humans do: "53 can only be a year and 15 cannot be a
month..." etc.

If no year can found, the function returns None, otherwise it returns
a "YYYY[-MM[-DD]]" string with all unambigous information.

Any unambigous date will be interpreted correctly, including
USAnian M/D/Y formats like "2/13/75".

Ambiguous strings "1/1/1960" will only return "1960", which is
good enough to sort artifacts chronologically.

The script can also be used interactively or as filter.

The code makes the following cultural assumptions:

* The textual names of the months.  Add to the MONTHS array if
  your language is not Danish or English.

* Dates written with exactly two "." or '-' separators are
  in either DMY or YMD format.

* Two digit years were only used [1932-1999]

* All dates are historical (See: YEAR_HIGH)

* Where multiple years or months are found, the first is used.
  (Ie: "Dec/Jan 84-85" returns "1984-12"

Enjoy,

Poul-Henning
