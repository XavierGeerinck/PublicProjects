using System;
using MLCarFilter.Models;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;

using Microsoft.ML;
using Microsoft.ML.Data;
using static Microsoft.ML.Transforms.NormalizingEstimator;

namespace MLCarFilter
{
    class Program
    {
        private static string trainingFilePath = "./car-train.csv";
        private static string testFilePath = "./car-test.csv";
        private static string modelOutputPath = "./Model.zip";

        static void Main(string[] args)
        {
            TrainModel();
            TestModel();
        }

        public static void TrainModel()
        {
            // Create ML Context with seed for repeteable/deterministic results
            MLContext mlContext = new MLContext(seed: 0);

            // STEP 1: Common data loading configuration
            IDataView trainingDataView = mlContext.Data.LoadFromTextFile<CarPoint>(trainingFilePath, hasHeader: true, separatorChar: ',');
            IDataView testDataView = mlContext.Data.LoadFromTextFile<CarPoint>(testFilePath, hasHeader: true, separatorChar: ',');

            // STEP 2: Common data process configuration with pipeline data transformations
            var dataProcessPipeline = mlContext.Transforms.CopyColumns(outputColumnName: "Label", inputColumnName: nameof(CarPoint.Speed_MPH))
                .Append(mlContext.Transforms.NormalizeMeanVariance(outputColumnName: "ThrottlePosition_Normalized", inputColumnName: nameof(CarPoint.ThrottlePosition)))
                .Append(mlContext.Transforms.NormalizeMeanVariance(outputColumnName: "Engine_RPM_Normalized", inputColumnName: nameof(CarPoint.Engine_RPM)))
                .Append(mlContext.Transforms.NormalizeMeanVariance(outputColumnName: "Acceleration_Gs_Normalized", inputColumnName: nameof(CarPoint.Acceleration_Gs)))
                .Append(mlContext.Transforms.Concatenate("Features", "ThrottlePosition_Normalized", "Engine_RPM_Normalized", "Acceleration_Gs_Normalized"));

            Console.WriteLine("================= Labels & Features ==================");
            Console.WriteLine($"Label:\n\t{nameof(CarPoint.Speed_MPH)}");
            Console.WriteLine($"Features: \n\t[V1] {nameof(CarPoint.ThrottlePosition)} \n\t[V2] {nameof(CarPoint.Engine_RPM)} \n\t[V3] {nameof(CarPoint.Acceleration_Gs)}");

            // STEP 3: Set the training algorithm, then create and config the modelBuilder - Selected Trainer (SDCA Regression algorithm)                            
            var trainer = mlContext.Regression.Trainers.Sdca(labelColumnName: "Label", featureColumnName: "Features");
            var trainingPipeline = dataProcessPipeline.Append(trainer);

            // STEP 4: Train the model fitting to the DataSet
            //The pipeline is trained on the dataset that has been loaded and transformed.
            Console.WriteLine("================= Training the model =================");
            var trainedModel = trainingPipeline.Fit(trainingDataView);

            // STEP 5: Evaluate the model and show accuracy stats
            Console.WriteLine("===== Evaluating Model's accuracy with Test data =====");

            IDataView predictions = trainedModel.Transform(testDataView);
            var metrics = mlContext.Regression.Evaluate(predictions, labelColumnName: "Label", scoreColumnName: "Score");

            // Common.ConsoleHelper.PrintRegressionMetrics(trainer.ToString(), metrics);

            // STEP 6: Save/persist the trained model to a .ZIP file
            mlContext.Model.Save(trainedModel, trainingDataView.Schema, modelOutputPath);

            Console.WriteLine("======================================================");
            Console.WriteLine("The model is saved to {0}", modelOutputPath);
        }

        public static void TestModel() 
        {
            // Create ML Context with seed for repeteable/deterministic results
            MLContext mlContext = new MLContext(seed: 0);

            // Common.ConsoleHelper.PrintRegressionMetrics(trainer.ToString(), metrics);

            var carPointSample = new CarPoint()
            {
                Time = "2018-04-08 10:32:55.390684",
                Seconds = 772.693372F,
                Latitude_Y_Degrees = 30.321299F,
                Longitude_X_Degrees = -97.75582299999999F,
                Distance_Miles = 7.96F,
                Speed_MPH = 30.647F,
                SteeringAngle = -0.9F,
                ThrottlePosition = 2F,
                Engine_RPM = 1624F,
                Lateral_Gs = -0.01F,
                Acceleration_Gs = -0.05F
            };

            ITransformer trainedModel;
            using (var stream = new FileStream(modelOutputPath, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                trainedModel = mlContext.Model.Load(stream, out var modelInputSchema);
            }

            // Create prediction engine related to the loaded trained model
            var predEngine = mlContext.Model.CreatePredictionEngine<CarPoint, CarPointSpeedPrediction>(trainedModel);

            //Score
            var resultprediction = predEngine.Predict(carPointSample);

            Console.WriteLine("======================================================");
            Console.WriteLine($"Predicted speed: {resultprediction.Speed_MPH:0.####}, actual speed: 30.647");
            Console.WriteLine("======================================================");
        }
    }
}
