```mermaid
flowchart TD
Google
subgraph Stanford_Reviews
  subgraph SR_copy_of_zds1_metadata
  SR_zds1_review1
  SR_zds1_review2
  end
end
subgraph Harvard_Dataverse
  subgraph HD_copy_of_zds1_metadata
  HR_zds1_review1
  HR_zds1_review2
  end
  subgraph HD_dataset2
  HD_ds2_review1
  end
  subgraph HD_dataset1
  no_reviewsHD@{ shape: rect, label: "[no reviews]" }
  end
end
subgraph Zenodo
  subgraph Z_dataset1
  no_reviewsZ@{ shape: rect, label: "[no reviews]" }
  end
end

Google -- crawls --> Zenodo
Google -- crawls --> Harvard_Dataverse
Z_dataset1 -.-> HD_copy_of_zds1_metadata
Z_dataset1 -.-> SR_copy_of_zds1_metadata
Google -- crawls --> Stanford_Reviews
```

- In this scenario, the Dataverse supports foreign datasets where the metadata is copied and reviews can be attached.
- How does Google handle reviews from both Harvard Dataverse and Stanford Reviews?
- What if Zenodo start supporting reviews?