from mav.Tasks.travel.tools import (
    cancel_calendar_event,
    create_calendar_event,
    get_day_calendar_events,
    search_calendar_events,
    send_email,
    check_restaurant_opening_hours,
    get_all_car_rental_companies_in_city,
    get_all_hotels_in_city,
    get_all_restaurants_in_city,
    get_car_fuel_options,
    get_car_price_per_day,
    get_car_rental_address,
    get_car_types_available,
    get_contact_information_for_restaurants,
    get_cuisine_type_for_restaurants,
    get_dietary_restrictions_for_all_restaurants,
    get_flight_information,
    get_hotels_address,
    get_hotels_prices,
    get_price_for_restaurants,
    get_rating_reviews_for_car_rental,
    get_rating_reviews_for_hotels,
    get_rating_reviews_for_restaurants,
    get_restaurants_address,
    get_user_information,
    reserve_car_rental,
    reserve_hotel,
    reserve_restaurant,
)

from mav.Tasks.task_suite import TaskSuite
from mav.Tasks.travel.environment import TravelEnvironment

from functools import partial
from deepdiff.diff import DeepDiff

tools = [
    cancel_calendar_event,
    create_calendar_event,
    get_day_calendar_events,
    search_calendar_events,
    send_email,
    check_restaurant_opening_hours,
    get_all_car_rental_companies_in_city,
    get_all_hotels_in_city,
    get_all_restaurants_in_city,
    get_car_fuel_options,
    get_car_price_per_day,
    get_car_rental_address,
    get_car_types_available,
    get_contact_information_for_restaurants,
    get_cuisine_type_for_restaurants,
    get_dietary_restrictions_for_all_restaurants,
    get_flight_information,
    get_hotels_address,
    get_hotels_prices,
    get_price_for_restaurants,
    get_rating_reviews_for_car_rental,
    get_rating_reviews_for_hotels,
    get_rating_reviews_for_restaurants,
    get_restaurants_address,
    get_user_information,
    reserve_car_rental,
    reserve_hotel,
    reserve_restaurant,
]

deepdiff_paths_to_exclude = [
    "root.inbox.sent",
    "root.inbox.received",
    "root.inbox.drafts",
    "root.responses",
    "root.model_fields_set",
    "root.calendar.initial_events",
    "root.inbox.initial_emails",
    "root.cloud_drive.initial_files",
]


TravelDeepDiff = partial(DeepDiff, exclude_paths=deepdiff_paths_to_exclude)

travel_task_suite = TaskSuite[TravelEnvironment](
    tools=tools,
    name="travel",
    environment_type=TravelEnvironment
)
