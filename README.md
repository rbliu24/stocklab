# stocklab

## Metaevaluate
- metadata: known data in the dependency evaluation phase (e.g. valid_date)
- internal id of stocks are not static

## Design choices
- stocklab expressions cannot contain curly-braces
- a single underscore in the expression means dont-care, otherwise expressions cannot start/end with underscore
