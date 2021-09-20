from unittest import TestCase
from beautiful_date import Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sept, Oct, Dec, hours, days

from gcsa.attachment import Attachment
from gcsa.attendee import Attendee, ResponseStatus
from gcsa.event import Event, Visibility
from gcsa.gadget import Gadget
from gcsa.recurrence import Recurrence, DAILY, SU, SA, MONDAY, WEEKLY
from gcsa.reminders import PopupReminder, EmailReminder
from gcsa.serializers.event_serializer import EventSerializer
from gcsa.util.date_time_util import insure_localisation

TEST_TIMEZONE = 'Pacific/Fiji'


class TestEvent(TestCase):
    def test_init(self):
        event = Event(
            'Breakfast',
            event_id='123',
            start=(1 / Feb / 2019)[9:00],
            end=(31 / Dec / 2019)[23:59],
            timezone=TEST_TIMEZONE,
            description='Everyday breakfast',
            location='Home',
            recurrence=[
                Recurrence.rule(freq=DAILY),
                Recurrence.exclude_rule(by_week_day=[SU, SA]),
                Recurrence.exclude_dates([
                    19 / Apr / 2019,
                    22 / Apr / 2019,
                    12 / May / 2019
                ])
            ],
            visibility=Visibility.PRIVATE,
            minutes_before_popup_reminder=15
        )

        self.assertEqual(event.summary, 'Breakfast')
        self.assertEqual(event.id, '123')
        self.assertEqual(event.start, insure_localisation((1 / Feb / 2019)[9:00], TEST_TIMEZONE))
        self.assertEqual(event.description, 'Everyday breakfast')
        self.assertEqual(event.location, 'Home')
        self.assertEqual(len(event.recurrence), 3)
        self.assertEqual(event.visibility, Visibility.PRIVATE)
        self.assertIsInstance(event.reminders[0], PopupReminder)
        self.assertEqual(event.reminders[0].minutes_before_start, 15)

    def test_init_no_end(self):
        start = 1 / Jun / 2019
        event = Event('Good day', start, timezone=TEST_TIMEZONE)
        self.assertEqual(event.end, start + 1 * days)

        start = insure_localisation((1 / Jul / 2019)[12:00], TEST_TIMEZONE)
        event = Event('Lunch', start, timezone=TEST_TIMEZONE)
        self.assertEqual(event.end, start + 1 * hours)

    def test_init_different_date_types(self):
        with self.assertRaises(TypeError):
            Event('Good day', start=(1 / Jan / 2019), end=(2 / Jan / 2019)[5:55], timezone=TEST_TIMEZONE)

    def test_add_attachment(self):
        e = Event('Good day', start=(1 / Aug / 2019), timezone=TEST_TIMEZONE)
        e.add_attachment('https://file.url', 'My file', "application/vnd.google-apps.document")

        self.assertIsInstance(e.attachments[0], Attachment)
        self.assertEqual(e.attachments[0].title, 'My file')

    def test_add_reminders(self):
        e = Event('Good day', start=(28 / Mar / 2019), timezone=TEST_TIMEZONE)

        self.assertEqual(len(e.reminders), 0)

        e.add_email_reminder(35)
        self.assertEqual(len(e.reminders), 1)
        self.assertIsInstance(e.reminders[0], EmailReminder)
        self.assertEqual(e.reminders[0].minutes_before_start, 35)

        e.add_popup_reminder(41)
        self.assertEqual(len(e.reminders), 2)
        self.assertIsInstance(e.reminders[1], PopupReminder)
        self.assertEqual(e.reminders[1].minutes_before_start, 41)

    def test_add_attendees(self):
        e = Event('Good day',
                  start=(17 / Jul / 2020),
                  timezone=TEST_TIMEZONE,
                  attendees=[
                      Attendee(email="attendee@gmail.com"),
                      "attendee2@gmail.com",
                  ])

        self.assertEqual(len(e.attendees), 2)
        e.add_attendee(Attendee("attendee3@gmail.com"))
        e.add_attendee(Attendee(email="attendee4@gmail.com"))
        self.assertEqual(len(e.attendees), 4)

        self.assertEqual(e.attendees[0].email, "attendee@gmail.com")
        self.assertEqual(e.attendees[1].email, "attendee2@gmail.com")
        self.assertEqual(e.attendees[2].email, "attendee3@gmail.com")
        self.assertEqual(e.attendees[3].email, "attendee4@gmail.com")

    def test_reminders_checks(self):
        with self.assertRaises(ValueError):
            Event('Too many reminders',
                  start=20 / Jul / 2020,
                  reminders=[EmailReminder()] * 6)

        with self.assertRaises(ValueError):
            Event('Default and overrides together',
                  start=20 / Jul / 2020,
                  reminders=EmailReminder(),
                  default_reminders=True)

        e = Event('Almost too many reminders',
                  start=20 / Jul / 2020,
                  reminders=[EmailReminder()] * 5)
        with self.assertRaises(ValueError):
            e.add_email_reminder()

    def test_str_repr(self):
        e = Event('Good event',
                  start=20 / Jul / 2020)
        self.assertEqual(str(e), '2020-07-20 - Good event')

        self.assertEqual(repr(e), '<Event 2020-07-20 - Good event>')

    def test_equal(self):
        dp = {
            'summary': 'Breakfast',
            'start': (1 / Feb / 2019)[9:00]
        }

        gadget_dp = {
            "type_": Gadget.ICON,
            "link": 'https://gadget.com',
            "icon_link": 'https://icon.com'
        }

        attachments_dp = {
            "file_url": 'https://file.com',
            "mime_type": "application/vnd.google-apps.map"
        }

        event1 = Event(
            **dp,
            event_id='123',
            end=(31 / Dec / 2019)[23:59],
            timezone=TEST_TIMEZONE,
            description='Everyday breakfast',
            location='Home',
            recurrence=Recurrence.rule(freq=DAILY),
            color='#254433',
            visibility=Visibility.PRIVATE,
            attendees='mail@gmail.com',
            gadget=Gadget('Gadget', **gadget_dp),
            attachments=Attachment('My doc', **attachments_dp),
            minutes_before_popup_reminder=15,
            other={"key": "value"}
        )

        self.assertEqual(event1, event1)
        self.assertNotEqual(Event(**dp), Event('Breakfast', start=(22 / Jun / 2020)[22:22]))

        self.assertNotEqual(Event(**dp, event_id='123'),
                            Event(**dp, event_id='abc'))

        self.assertNotEqual(Event(**dp, description='Desc1'),
                            Event(**dp, description='Desc2'))

        self.assertNotEqual(Event(**dp, location='Home'),
                            Event(**dp, location='Work'))

        self.assertNotEqual(Event(**dp, recurrence=Recurrence.rule(freq=DAILY)),
                            Event(**dp, recurrence=Recurrence.rule(freq=WEEKLY)))

        self.assertNotEqual(Event(**dp, color='#254433'),
                            Event(**dp, color='#ffffff'))

        self.assertNotEqual(Event(**dp, visibility=Visibility.PRIVATE),
                            Event(**dp, visibility=Visibility.PUBLIC))

        self.assertNotEqual(Event(**dp, attendees='mail1@gmail.com'),
                            Event(**dp, attendees='mail2@gmail.com'))

        self.assertNotEqual(Event(**dp, gadget=Gadget('Gadget1', **gadget_dp)),
                            Event(**dp, gadget=Gadget('Gadget2', **gadget_dp)))

        self.assertNotEqual(Event(**dp, attachments=Attachment('Attachment1', **attachments_dp)),
                            Event(**dp, attachments=Attachment('Attachment2', **attachments_dp)))

        self.assertNotEqual(Event(**dp, minutes_before_email_reminder=10),
                            Event(**dp, minutes_before_popup_reminder=10))

        self.assertNotEqual(Event(**dp, other={"key1": "value1"}),
                            Event(**dp, other={"key2": "value2"}))

    def test_ordering(self):
        e1 = Event('Good day', start=(28 / Sept / 2020), end=(30 / Sept / 2020), timezone=TEST_TIMEZONE)
        e2 = Event('Good day', start=(28 / Sept / 2020), end=(16 / Oct / 2020), timezone=TEST_TIMEZONE)
        e3 = Event('Good day', start=(29 / Sept / 2020), end=(30 / Sept / 2020), timezone=TEST_TIMEZONE)
        e4 = Event('Good day', start=(29 / Sept / 2020)[22:22], end=(30 / Sept / 2020)[15:15], timezone=TEST_TIMEZONE)
        e5 = Event('Good day', start=(29 / Sept / 2020)[22:22], end=(30 / Sept / 2020)[18:15], timezone=TEST_TIMEZONE)
        e6 = Event('Good day', start=(29 / Sept / 2020)[23:22], end=(30 / Sept / 2020)[18:15], timezone=TEST_TIMEZONE)

        self.assertEqual(list(sorted([e5, e6, e1, e3, e2, e4])), [e1, e2, e3, e4, e5, e6])

        self.assertTrue(e1 < e2)
        self.assertTrue(e3 > e2)
        self.assertTrue(e5 >= e2)
        self.assertTrue(e2 >= e2)
        self.assertTrue(e5 <= e5)
        self.assertTrue(e5 <= e6)


class TestEventSerializer(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_to_json(self):
        e = Event('Good day', start=(28 / Sept / 2019), timezone=TEST_TIMEZONE)
        event_json = {
            'summary': 'Good day',
            'start': {'date': '2019-09-28'},
            'end': {'date': '2019-09-29'},
            'recurrence': [],
            'visibility': 'default',
            'attendees': [],
            'reminders': {'useDefault': False},
            'attachments': []
        }
        self.assertDictEqual(EventSerializer.to_json(e), event_json)

        e = Event('Good day', start=(28 / Oct / 2019)[11:22:33], timezone=TEST_TIMEZONE)
        event_json = {
            'summary': 'Good day',
            'start': {'dateTime': '2019-10-28T11:22:33+12:00', 'timeZone': TEST_TIMEZONE},
            'end': {'dateTime': '2019-10-28T12:22:33+12:00', 'timeZone': TEST_TIMEZONE},
            'recurrence': [],
            'visibility': 'default',
            'attendees': [],
            'reminders': {'useDefault': False},
            'attachments': []
        }
        self.assertDictEqual(EventSerializer.to_json(e), event_json)

    def test_to_json_recurrence(self):
        e = Event('Good day',
                  start=(1 / Jan / 2019)[11:22:33],
                  end=(1 / Jan / 2020)[11:22:33],
                  timezone=TEST_TIMEZONE,
                  recurrence=[
                      Recurrence.rule(freq=DAILY),
                      Recurrence.exclude_rule(by_week_day=MONDAY),
                      Recurrence.exclude_dates([
                          19 / Apr / 2019,
                          22 / Apr / 2019,
                          12 / May / 2019
                      ])
                  ])
        event_json = {
            'summary': 'Good day',
            'start': {'dateTime': '2019-01-01T11:22:33+13:00', 'timeZone': TEST_TIMEZONE},
            'end': {'dateTime': '2020-01-01T11:22:33+13:00', 'timeZone': TEST_TIMEZONE},
            'recurrence': [
                'RRULE:FREQ=DAILY;WKST=SU',
                'EXRULE:FREQ=DAILY;BYDAY=MO;WKST=SU',
                'EXDATE;VALUE=DATE:20190419,20190422,20190512'
            ],
            'visibility': 'default',
            'attendees': [],
            'reminders': {'useDefault': False},
            'attachments': []
        }
        self.assertDictEqual(EventSerializer.to_json(e), event_json)

    def test_to_json_attachments(self):
        e = Event('Good day',
                  start=(1 / Jan / 2019)[11:22:33],
                  timezone=TEST_TIMEZONE,
                  attachments=[
                      Attachment('My file1', 'https://file.url1', "application/vnd.google-apps.document"),
                      Attachment('My file2', 'https://file.url2', "application/vnd.google-apps.document")
                  ])
        event_json = {
            'summary': 'Good day',
            'start': {'dateTime': '2019-01-01T11:22:33+13:00', 'timeZone': TEST_TIMEZONE},
            'end': {'dateTime': '2019-01-01T12:22:33+13:00', 'timeZone': TEST_TIMEZONE},
            'recurrence': [],
            'visibility': 'default',
            'attendees': [],
            'reminders': {'useDefault': False},
            'attachments': [
                {
                    'title': 'My file1',
                    'fileUrl': 'https://file.url1',
                    'mimeType': 'application/vnd.google-apps.document'
                },
                {
                    'title': 'My file2',
                    'fileUrl': 'https://file.url2',
                    'mimeType': 'application/vnd.google-apps.document'
                }
            ]
        }
        self.assertDictEqual(EventSerializer.to_json(e), event_json)

    def test_to_json_reminders(self):
        e = Event('Good day',
                  start=(1 / Jan / 2019)[11:22:33],
                  timezone=TEST_TIMEZONE,
                  minutes_before_popup_reminder=30,
                  minutes_before_email_reminder=120)
        event_json = {
            'summary': 'Good day',
            'start': {'dateTime': '2019-01-01T11:22:33+13:00', 'timeZone': TEST_TIMEZONE},
            'end': {'dateTime': '2019-01-01T12:22:33+13:00', 'timeZone': TEST_TIMEZONE},
            'recurrence': [],
            'visibility': 'default',
            'attendees': [],
            'reminders': {
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'email', 'minutes': 120}
                ],
                'useDefault': False
            },
            'attachments': []
        }
        self.assertDictEqual(EventSerializer.to_json(e), event_json)

    def test_to_json_attendees(self):
        e = Event('Good day',
                  start=(1 / Jul / 2020)[11:22:33],
                  timezone=TEST_TIMEZONE,
                  attendees=[
                      Attendee(email='attendee@gmail.com', response_status=ResponseStatus.NEEDS_ACTION),
                      Attendee(email='attendee2@gmail.com', response_status=ResponseStatus.ACCEPTED),
                  ])
        event_json = {
            'summary': 'Good day',
            'start': {'dateTime': '2020-07-01T11:22:33+12:00', 'timeZone': TEST_TIMEZONE},
            'end': {'dateTime': '2020-07-01T12:22:33+12:00', 'timeZone': TEST_TIMEZONE},
            'recurrence': [],
            'visibility': 'default',
            'attendees': [
                {'email': 'attendee@gmail.com', 'responseStatus': ResponseStatus.NEEDS_ACTION},
                {'email': 'attendee2@gmail.com', 'responseStatus': ResponseStatus.ACCEPTED},
            ],
            'reminders': {'useDefault': False},
            'attachments': []
        }
        self.assertDictEqual(EventSerializer.to_json(e), event_json)

        e = Event('Good day2',
                  start=20 / Jul / 2020,
                  default_reminders=True)
        event_json = {
            'summary': 'Good day2',
            'start': {'date': '2020-07-20'},
            'end': {'date': '2020-07-21'},
            'recurrence': [],
            'visibility': 'default',
            'attendees': [],
            'reminders': {'useDefault': True},
            'attachments': []
        }
        self.assertDictEqual(EventSerializer.to_json(e), event_json)

    def test_to_object(self):
        event_json = {
            'summary': 'Good day',
            'description': 'Very good day indeed',
            'location': 'Prague',
            'start': {'dateTime': '2019-01-01T11:22:33', 'timeZone': TEST_TIMEZONE},
            'end': {'dateTime': '2019-01-01T12:22:33', 'timeZone': TEST_TIMEZONE},
            'recurrence': [
                'RRULE:FREQ=DAILY;WKST=SU',
                'EXRULE:FREQ=DAILY;BYDAY=MO;WKST=SU',
                'EXDATE:VALUE=DATE:20190419,20190422,20190512'
            ],
            'visibility': 'public',
            'attendees': [
                {'email': 'attendee@gmail.com', 'responseStatus': ResponseStatus.NEEDS_ACTION},
                {'email': 'attendee2@gmail.com', 'responseStatus': ResponseStatus.ACCEPTED},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'email', 'minutes': 120}
                ]
            },
            'attachments': [
                {
                    'title': 'My file1',
                    'fileUrl': 'https://file.url1',
                    'mimeType': 'application/vnd.google-apps.document'
                },
                {
                    'title': 'My file2',
                    'fileUrl': 'https://file.url2',
                    'mimeType': 'application/vnd.google-apps.document'
                }
            ]
        }

        serializer = EventSerializer(event_json)
        event = serializer.get_object()

        self.assertEqual(event.summary, 'Good day')
        self.assertEqual(event.start, insure_localisation((1 / Jan / 2019)[11:22:33], TEST_TIMEZONE))
        self.assertEqual(event.end, insure_localisation((1 / Jan / 2019)[12:22:33], TEST_TIMEZONE))
        self.assertEqual(event.description, 'Very good day indeed')
        self.assertEqual(event.location, 'Prague')
        self.assertEqual(len(event.recurrence), 3)
        self.assertEqual(event.visibility, Visibility.PUBLIC)
        self.assertEqual(len(event.attendees), 2)
        self.assertIsInstance(event.reminders[0], PopupReminder)
        self.assertEqual(event.reminders[0].minutes_before_start, 30)
        self.assertIsInstance(event.reminders[1], EmailReminder)
        self.assertEqual(event.reminders[1].minutes_before_start, 120)
        self.assertEqual(len(event.attachments), 2)
        self.assertIsInstance(event.attachments[0], Attachment)
        self.assertEqual(event.attachments[0].title, 'My file1')

        event_json_str = """{
            "summary": "Good day",
            "description": "Very good day indeed",
            "location": "Prague",
            "start": {"date": "2020-07-20"},
            "end": {"date": "2020-07-22"}
        }"""

        event = EventSerializer.to_object(event_json_str)

        self.assertEqual(event.summary, 'Good day')
        self.assertEqual(event.description, 'Very good day indeed')
        self.assertEqual(event.location, 'Prague')
        self.assertEqual(event.start, 20 / Jul / 2020)
        self.assertEqual(event.end, 22 / Jul / 2020)
