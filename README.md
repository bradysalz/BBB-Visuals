# BBB-Visuals

Some code I wrote to analyze one of my favorite group chats in college. There
are probably better ways to do this now, but at the time I used a AutoHotKey to
scroll through and save an entire `m.facbook.com` chat to an HTML file. There
were better ways of doing this through an API or something, but it's been a
fun side project.

If I have time, I'll post some anonymized results here. No promises though!

## Getting Started

If you have a similar file, maybe this will work for you? Clone the repo, and

```
pip install -r requirements.txt
```

Due to the types, it requires Python v3.5+. After that, you should:

* Run `./database.py` to generate the database
* Change the `FNAME` constant at the top of `parse.py` to point to your data
* Run `./parse.py`

If it all works out, you should have a nice database to work with! If not,
well, you can shoot me a message I guess?

## Contributing

Want to help out? Cool! I like using:

* `yapf` for formatting my code
* `flake8` for linting my code
* `pyre` for type checking my code

Please use those too!
