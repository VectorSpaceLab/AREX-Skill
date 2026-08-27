# Python 3 basics from the legacy snippet file

These examples modernize the tiny patterns preserved in `basic_commands.py`.

## enumerate

Legacy pattern:

```python
a = ['a', 'b', 'c', 'd', 'e']
for index, item in enumerate(a):
    print index, item
```

Modern Python 3:

```python
a = ['a', 'b', 'c', 'd', 'e']
for index, item in enumerate(a):
    print(index, item)
```

Why this changed:
- `print` became a function in Python 3.
- `enumerate()` itself is unchanged.
- Use `enumerate(a, start=1)` if you want one-based numbering.

## Join a list into a string

Legacy pattern:

```python
list1 = ['1', '2', '3']
str1 = ''.join(list1)
```

Modern Python 3:

```python
items = ['1', '2', '3']
text = ''.join(items)

numbers = [1, 2, 3]
text = ''.join(map(str, numbers))
```

Why this changed:
- `join()` only accepts strings.
- Convert non-string items first with `map(str, ...)` or a comprehension.
- The separator controls how the pieces are glued together; `''` means no separator.

## str.find

Legacy signature note from the source file:

```python
str.find(str2, beg=0 end=len(string))
```

Modern Python 3:

```python
haystack = 'this is string example....wow!!!'
needle = 'exam'

print(haystack.find(needle))
print(haystack.find(needle, 10))
print(haystack.find(needle, 40))
```

Why this changed:
- `find` is a method on the string object, so call `haystack.find(...)`.
- It returns the first index or `-1` if the substring is absent.
- Use `index()` instead if you want an exception when the substring is missing.

## 2D-list column extraction

Legacy pattern:

```python
matrix = [[0 for _ in range(5)] for _ in range(5)]
matrix[0][0] = 1
matrix[4][0] = 5

print(matrix[0][0])
print(matrix[4][0])

A = [[1, 2, 3, 4],
     [5, 6, 7, 8]]

def column(matrix, i):
    return [row[i] for row in matrix]
```

Modern Python 3:

```python
matrix = [[0 for _ in range(5)] for _ in range(5)]
matrix[0][0] = 1
matrix[4][0] = 5

print(matrix[0][0])
print(matrix[4][0])

def column(matrix, i):
    return [row[i] for row in matrix]

A = [[1, 2, 3, 4],
     [5, 6, 7, 8]]
print(column(A, 1))
```

Why this changed:
- Lowercase `matrix` is clearer than `Matrix` for a plain list variable.
- `_` signals that the loop variable is unused.
- The list-comprehension column extractor is already valid in Python 3; the main modernization is the print syntax and naming.
- If rows may be ragged, guard with `if i < len(row)` before indexing.

## Rule of thumb

If the request is really about pandas or NumPy column handling, route to the pandas topic family instead of stretching the plain-list example.
