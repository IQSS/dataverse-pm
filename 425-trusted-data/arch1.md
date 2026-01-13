```mermaid
flowchart TD
Google
subgraph Harvard_Reviews
  subgraph HR_copy_of_zds1_metadata
  HR_zds1_review1
  HR_zds1_review2
  end
end
subgraph Stanford_Reviews
  subgraph SR_copy_of_zds1_metadata
  SR_zds1_review1
  SR_zds1_review2
  end
end
subgraph Harvard_Dataverse
  subgraph HD_dataset2
  HD_ds1_review1
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

Google -- crawls --> Harvard_Dataverse
Google -- crawls --> Zenodo
Google -- crawls --> Harvard_Reviews
Z_dataset1 -.-> HR_copy_of_zds1_metadata
Z_dataset1 -.-> SR_copy_of_zds1_metadata
Google -- crawls --> Stanford_Reviews
```

- Harvard Reviews is not running Dataverse. It's a separate app.
- When Google crawls, does it trust only reviews from Harvard Reviews? What about Stanford Reviews?
- In this scenario, Dataverse (including Harvard Dataverse) supports reviews of datasets it controls.
- What if Stanford Reviews starts reviewing datasets from Harvard Dataverse? Does Google trust those reviews?
- What happens when Zendo start supporting reviews? Does Google start aggregating reviews?