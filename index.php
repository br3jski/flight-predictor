<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Predictor v0.1</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {
            background-color: #212529;
            color: #fff;
        }
        .form-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: #343a40;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">Flight Predictor v0.1</h1>
        <div class="form-container">
            <form method="get" action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]);?>">
                <div class="form-group">
                    <label for="callsign">Callsign:</label>
                    <input type="text" class="form-control" id="callsign" name="callsign" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block" name="action" value="predict">Predict Route</button>
                <button type="submit" class="btn btn-secondary btn-block mt-2" name="action" value="list_departures">List Departures</button>
            </form>

            <?php
            if ($_SERVER["REQUEST_METHOD"] == "GET" && isset($_GET["action"])) {
                $callsign = strtoupper($_GET["callsign"]);
                $action = $_GET["action"];

                if ($action == "predict") {
                    $ch = curl_init();
                    curl_setopt($ch, CURLOPT_URL, "http://api.cloudvance.eu:5000/predict?callsign=" . urlencode($callsign));
                    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

                    $response = curl_exec($ch);
                    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                    curl_close($ch);

                    if ($http_code == 200) {
                        $response_data = json_decode($response, true);
                        $dep_icao = $response_data["dep_icao"];
                        $arr_icao = $response_data["arr_icao"];

                        $airports_file = "airports.json";
                        $airports_data = file_get_contents($airports_file);
                        $airports = json_decode($airports_data, true);

                        $dep_airport_name = "";
                        $arr_airport_name = "";

                        foreach ($airports as $airport) {
                            if ($airport["icao"] == $dep_icao) {
                                $dep_airport_name = $airport["name"];
                                break;
                            }
                        }

                        foreach ($airports as $airport) {
                            if ($airport["icao"] == $arr_icao) {
                                $arr_airport_name = $airport["name"];
                                break;
                            }
                        }

                        echo "<div class='mt-4'>";
                        echo "<p>Callsign: " . $response_data["callsign"] . "</p>";
                        echo "<p>Departure: " . $dep_icao . ", " . ($dep_airport_name ? $dep_airport_name : "Unknown Airport") . "</p>";
                        echo "<p>Arrival: " . $arr_icao . ", " . ($arr_airport_name ? $arr_airport_name : "Unknown Airport") . "</p>";
                        echo "</div>";
                    } elseif ($http_code == 404) {
                        echo "<div class='mt-4 alert alert-warning'>No information for callsign " . $callsign . "</div>";
                    } elseif ($http_code == 500) {
                        echo "<div class='mt-4 alert alert-danger'>Server error</div>";
                    } else {
                        echo "<div class='mt-4 alert alert-danger'>Unknown error</div>";
                    }
                } elseif ($action == "list_departures") {
                    $dep_icao = $callsign;

                    $ch = curl_init();
                    curl_setopt($ch, CURLOPT_URL, "http://api.cloudvance.eu:5000/flights_from_airport?dep_icao=" . urlencode($dep_icao));
                    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

                    $response = curl_exec($ch);
                    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                    curl_close($ch);

                    if ($http_code == 200) {
                        $response_data = json_decode($response, true);

                        $airports_file = "airports.json";
                        $airports_data = file_get_contents($airports_file);
                        $airports = json_decode($airports_data, true);

                        $dep_airport_name = "";

                        foreach ($airports as $airport) {
                            if ($airport["icao"] == $dep_icao) {
                                $dep_airport_name = $airport["name"];
                                break;
                            }
                        }

                        echo "<h4>Departures from " . $dep_icao . ", " . ($dep_airport_name ? $dep_airport_name : "Unknown Airport") . "</h4>";
                        echo "<table class='table table-dark'>";
                        echo "<thead><tr><th>Callsign</th><th>Arrival</th></tr></thead>";
                        echo "<tbody>";

                        foreach ($response_data as $flight) {
                            $arr_icao = $flight["arr_icao"];
                            $arr_airport_name = "";

                            foreach ($airports as $airport) {
                                if ($airport["icao"] == $arr_icao) {
                                    $arr_airport_name = $airport["name"];
                                    break;
                                }
                            }

                            echo "<tr>";
                            echo "<td>" . $flight["callsign"] . "</td>";
                            echo "<td>" . $arr_icao . ", " . ($arr_airport_name ? $arr_airport_name : "Unknown Airport") . "</td>";
                            echo "</tr>";
                        }

                        echo "</tbody>";
                        echo "</table>";
                    } elseif ($http_code == 404) {
                        echo "<div class='mt-4 alert alert-warning'>No flights found for the provided dep_icao</div>";
                    } elseif ($http_code == 500) {
                        echo "<div class='mt-4 alert alert-danger'>Server error</div>";
                    } else {
                        echo "<div class='mt-4 alert alert-danger'>Unknown error</div>";
                    }
                }
            }
            ?>
        </div>
    </div>
</body>
</html>