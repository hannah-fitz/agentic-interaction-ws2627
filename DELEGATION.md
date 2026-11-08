# Delegation: assignment 2

## 1. Action Classification

| No. | Action | Decision | Justification |
|---|---|---|---|
| 1 | Read the appointments of a day | alone | Reading calendar information is a passive action and does not change anything. |
| 2 | Look up the weather | alone | Only gathering public information; reading access doesn’t change anything and has no consequences in this case. |
| 3 | Search train connections | alone | Not different from the weather: Only gathering public information; reading access doesn’t change anything and has no consequences in this case. |
| 4 | Read notes | alone | Reading personal notes does not modify them or share any information. |
| 5 | Create a personal block in the calendar (e.g. travel time, no other attendees) | approval | Any changes to the calendar can have consequences to the person’s life (late to meetings, missing appointments etc). The agent should have the ability to create entries as this can be very useful, but it should always ask for confirmation to make the user aware of it and prevent stress.  |
| 6 | Reschedule an appointment with other attendees | approval | Similar to 5, the user probably wants to prevent changes to be made without notice for his planning. On top of that, it affects other people’s schedules. The user should confirm the change first. |
| 7 | Book a train ticket | approval | There is a financial commitment involved. Booking a ticket might be difficult or costly to reverse, so confirmation is essential here. |
| 8 | Send a message to third parties | approval | Communication to others on behalf of the user might not be reversible and can have consequences for relationships. The user probably wants to keep control over his chats, so confirmation should be demanded. |
| 9 | Create a note | alone | Creating a personal note is reversible, does not affect other people and can be a communication method between agent and person. It doesn’t neccassarily need confirmation. |
| 10 | Delete a note | approval | Deleting information can result in permanent data loss. The user should confirm before deletion. |


## 2. Delegation Rule

The agent may perform actions alone if they only involve reading information that is public or access was granted to or if changes are reversible, while actions that affect other people, involve financial commitments, or permanently modify or delete information require the user's approval. 


## 3. Observations from the Role Play

1. Information gathering and taking action are two different things. For example, searching for train connections is harmless, while actually booking a ticket could lead to financial damage.

2. Actions that affect other people need special attention. For example, sending a message to colleagues or rescheduling a meeting should not happen without the user's approval.

3. Reversibility matters. Creating a personal note is easy to undo, whereas deleting notes could result in losing important information.

4. Communicate sources for statements and recommendations clearly. In case the agent jumps to wrong conclusions, communicating what made it think this way will prevent mistakes as the user has a chance to notice misinterpretation.

