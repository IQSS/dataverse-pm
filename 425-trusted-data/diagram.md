```mermaid
flowchart LR
subgraph Google
subgraph DataCommons
DCDataset1
end
DatasetSearch
Search
end

subgraph Dataverse
Dataset1 --> Collection1
Collection1 -- not Croissant --> Search
Review2 --> DCDataset1
Review2 -- ? --> DatasetSearch
Dataset1 --> File1
File1 -- not Croissant --> Search
Review1 --> Dataset1 
Review1 -- ? --> DatasetSearch
Dataset1 -- 🥐 --> DatasetSearch
end
```
