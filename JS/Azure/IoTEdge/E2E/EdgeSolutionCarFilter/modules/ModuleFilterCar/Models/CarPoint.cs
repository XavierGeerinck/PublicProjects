using Microsoft.ML.Data;

namespace ModuleFilterCar.Models
{
    public class CarPoint
    {
        [LoadColumn(0)]
        public string Time { get; set; }

        [LoadColumn(1)]
        public float Seconds { get; set; }

        [LoadColumn(2)]
        public float Latitude_Y_Degrees { get; set; }

        [LoadColumn(3)]
        public float Longitude_X_Degrees { get; set; }

        [LoadColumn(4)]
        public float Distance_Miles { get; set; }

        [LoadColumn(5)]
        public float Speed_MPH { get; set; }

        [LoadColumn(6)]
        public float SteeringAngle { get; set; }

        [LoadColumn(7)]
        public float ThrottlePosition { get; set; }

        [LoadColumn(8)]
        public float Engine_RPM { get; set; }

        [LoadColumn(9)]
        public float Lateral_Gs { get; set; }

        [LoadColumn(10)]
        public float Acceleration_Gs { get; set; }
    }
}