# seed-content.json format

{
  "emails": [ { "subject": "<PREFIX>...", "html_body": "<p><b>SAMPLE DATA ...</b></p><p><b>From:</b> ...<br><b>To:</b> ...<br><b>Sent:</b> ...</p><p>Body</p>" } ],
  "teams_messages": [ "<b><PREFIX>Teams thread (simulated) – #Channel</b><br><i>Sample data – fictional</i><br><br><b>Name, date time:</b> text<br>..." ],
  "calendar_events": [ { "subject": "<PREFIX>...", "start": "YYYY-MM-DDTHH:MM:SS", "end": "YYYY-MM-DDTHH:MM:SS", "is_all_day": false, "location": "Microsoft Teams", "show_as": "busy" } ]
}

Rules
- Every subject and Teams message starts with the prefix, so setup can skip duplicates and reset can find items.
- Emails go to the signed-in user only; put the simulated sender, recipients and date in the body.
- All-day events: start at 00:00 and end at 00:00 the next day, with "is_all_day": true and "show_as": "free".
- No attendees and no online meeting links.
