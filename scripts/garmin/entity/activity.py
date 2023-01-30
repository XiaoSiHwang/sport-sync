class Activity:
    def __init__(self, activityId, activityName, activityType, startTimeLocal, calories, averageHR) -> None:
        self.activityId = activityId
        self.activityName = activityName
        self.activityType = activityType
        self.startTimeLocal = startTimeLocal
        self.calories = calories
        self.averageHR = averageHR