This is one of the core feature of BBOXHelper, its ability to order the blocks of text in a logial reading manner. 

If you look at our [Simple page layout](/examples/scan1/), the middle block of text is a 2 column layout: you will read the first column then continue to the next column naturally without event thinking about it. 

Well this is this natural reading order of things in a page, our default sorting algorythm tries to emulate. 
The implementation is done in the method named BBoxSort.contoursSort(...)

## Default sorting Algorithm 

It is the best algo I could came up with so far. Let me go through it a bit. 

Ultimate Goal : Generate a **blockid** for each block of text which we can sort upon, matching a certain natural reading order.

To generate a blockid I need first to understand where the blocks stands. 

Inspired by the following [stackoverflow answer](https://stackoverflow.com/questions/58903071/i-want-to-sort-the-words-extracted-from-image-in-order-of-their-occurence-using) contributed by [J-D](https://stackoverflow.com/users/10699171/j-d), the default sorting algo implements the following tasks

### First round: Vertical grouping
Find regions on the Y axis separated by empty regions:
- Empty region is a region on the Y axis where there is no bounding boxes
- By opposite we can then find regions on the Y Axis containing existing boxes
*See how blocks of text are grouped vertically like in the stackoverflow answer.*
For each non-empty region,
- ascending sort on their opposite axis 
- add a sequence number to each belonging block + regularization value

I then repeat the same operation horizontally so I can handle the 2-columns of text locating on the same vertical group. 

### Second round: Horizontal grouping 
Find regions on the X axis separated by empty regions:
- Empty region is a region on the X axis where there is no bounding boxes
- By opposite we can then find regions on the X Axis containing existing boxes
For each non-empty region,
- ascending sort on their opposite axis 
- add a sequence number to each belonging block + regularization value

At the end, each block has a blockid which we can sort ascendantly. 

This isn't perfect by all means, I'll be happy to receive feedback on this or welcome contributors to enhance this algorithm. 

## Others sorting algorithms

I'm providing few other "simplier" examples of sorting algorythm for convenience. Check the **BBoxSort** class in **bboxutils.py**.

## Implement your own sorting algorithm 

You can also implement your own algorithm defined as class method.

Define a class then function signature should be as follows 

```python
class myClass():
    @classmethod
    def mySort(cls,pageId,width,height,blocks):
        #...
        sorted=[]
        # Do your thing here with the incoming blocks
        #...
        return sorted
```

```python
# Call the processing of your choice with the sortingAlgo parameter pointing to your own class
bboxresponse=BBoxHelper().processAzureOCRResponse(ocrresponse,sortingAlgo=myClass.mySort)
```

