#set document(title: [$title$], author: "PortaPack Mayhem Wiki")
#set page(
  paper: "a4",
  margin: (x: 22mm, y: 20mm),
  numbering: "1",
)
#set text(font: "New Computer Modern", size: 10pt)
#set par(justify: true, leading: 0.62em)
#set heading(numbering: "1.1")
#let horizontalrule = line(length: 100%)
#show heading.where(level: 1): it => block(above: 1.6em, below: 0.8em, text(size: 20pt, weight: "bold", it))
#show heading.where(level: 2): it => block(above: 1em, below: 0.45em, text(size: 15pt, weight: "bold", it))
#show heading.where(level: 3): it => block(above: 0.8em, below: 0.35em, text(size: 12pt, weight: "bold", it))
#show raw: set text(size: 8.5pt)
#show link: set text(fill: rgb("#0645ad"))
#show image: it => block(above: 0.6em, below: 0.6em, align(center, it))

#align(center)[
  #text(size: 24pt, weight: "bold")[$title$] \
  #text(size: 13pt)[$subtitle$] \
  #v(1em)
  #text(size: 9pt)[Generated from the selected GitHub wiki pages.]
]

#pagebreak()
#outline(title: "Contents", depth: 3)
#pagebreak()

$body$
