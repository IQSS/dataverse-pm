**OJS SOP**

All email samples can be found [here](https://app.smartsheet.com/sheets/mcjCHHqqWQ4QFMQJg3GQCPGjmgQx59FC7gW7p4X1?view=grid)

**Submission Process**

1. It’s important to note that an **Author** must be [registered](https://drive.google.com/file/d/1UmVNTm8G1QtnpiseXxzv2Rg1iyhzBeWx/view?usp=drive_link) before submitting their research document
2. The **Author** submits their research document ([Author Directions](https://drive.google.com/file/d/1BVlcoZKkQTXKKyEmtx467Rn2Ov_pTg84/view?usp=drive_link))
3. The **Author** completes their submission, and the following emails are sent automatically
    1. SUBMISSION_ACK (Author)
    2. NOTIFICATION (Managing Editor)
4. Once the **Managing Editor** receives the NOTIFICATION email, they log into OJS and review the submission. ([Managing Editor Directions](https://docs.google.com/presentation/d/14IwJc7XyeZbT2anLyolSnDDxZno8ULbn/edit?usp=drive_link&ouid=101167688271837364090&rtpof=true&sd=true))
    1. EDITOR_DECISION_INITIAL_DECLINE (Author) is sent to the author to notify them that their submission is not eligible for PPR
    2. PPR_SUBMISSION_APPROVED (Author) is sent to the author to notify them that their submission is eligible for PPR

**Review Process**

1. Once the **Associate Editor** receives an assignment email (EDITOR_ASSIGN), they should log into the system to assign a Reviewer. ([Associate Editor directions](https://docs.google.com/presentation/d/1EB6PmTQIMOPKGO4DeOkQVraezi8hyd7J/edit?usp=drive_link&ouid=101167688271837364090&rtpof=true&sd=true))
2. These emails are sent during the Reviewer process
    1. **Request Review Emails**
        1. REVIEW_REQUEST_ONECLICK is sent to the Reviewer to request a review
            - REVIEW_CONFIRM_:_ The Reviewer accepted the review
            - REVIEW_DECLINE: The Reviewer declined the review
        2. PPR_REVIEW_REQUEST_DUE_DATE_REVIEWER is sent to the Reviewer when they haven’t responded to the request for review. The Associate Editors clicks the "Send Reminder" button next to a Reviewer's name
        3. PPR_REQUESTED_REVIEWER_UNASSIGN is sent to the Reviewer when they haven’t responded, and it’s time to move on to another Reviewer. The Associate Editor clicks the "Unassign Reviewer" under the Reviewer's name
    2. **Accepted Review Emails**
        1. PR_REVIEW_DUE_DATE_REVIEWER is a reminder sent to the Reviewer two days before their review is due
        2. REVIEW_REMIND_ONECLICK is sent to the Reviewer when they have missed their review due date. The Associate Editors clicks the "Send Reminder" button next to a Reviewer's name
        3. PPR_CONFIRMED_REVIEWER_UNASSIGN is sent to the Reviewer when they missed their review due date and it’s time to move on to another Reviewer. The Associate Editor clicks the "Cancel Reviewer” under the Reviewer's name
        4. PPR_REVIEW_SUBMITTED is sent to the reviewer once they upload and click the "Submit Review" blue button
        5. REVIEW_ACK is sent to the Reviewer once the review is completed letting them know someone will get in touch for payment. The Associate Editor clicks the "Thank Reviewer" button next to the Reviewers name
3. This email goes out once a review is late.
    1. PPR_REVIEW_DUE_DATE_WITH_FILES_REVIEWER is sent to the reviewer once they upload the review to the system, but don’t click “submit” to finalize the review before it is due
    2. PPR_REVIEW_PENDING_WITH_FILES_REVIEWER is sent to the reviewer once they upload the review to the system, but don’t click “submit” to finalize the review after it is due
    3. PPR_REVIEW_DUE_DATE_EDITOR is sent when a review or response is overdue to let the Associate Editor know they need to login and check on their review
4. This email goes out once a review has been completed and the Associate Editor sends it back to the Author.
    1. EDITOR_DECISION_REVISION is sent to the Author with their review attached. The Associate Editor clicks the "Send Review to Author" button under the submission

**Survey Process**

PPR values the users’ experience using OJS. There are two types of survey: one is to see how users (both authors and reviewers) like OJS submission system, the other is to see how the authors benefit from the reviewers.

1. The system will automatically send a survey to the author asking them how convenient they use OJS to make a submission. Noted that only a first-time author will receive the survey. With that said, if the author makes multiple submissions in the future, they won’t receive the survey. Anymore.
2. The system will automatically send a survey to the reviewer asking them how convenient they use OJS to make a review.
3. PPR_REVIEW_SENT_AUTHOR is sent to the authors a week after they receive the review to see how they benefit from the reviewer.
