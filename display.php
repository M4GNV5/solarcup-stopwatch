<!DOCTYPE html>
<html>
	<body>
		<table>
			<tr>
				<th align="left">Platz</th>
				<th align="left">Zeit</th>
				<th align="left">Team</th>
				<th align="left">Name</th>
			</tr>
			<?php
				$scores = file_get_contents("./../output.csv");
				$scores = explode("\n", $scores);
				$scores = array_map(function($x)
				{
					$result = explode(",", $x);
					$result[2] = (float)$result[2];
					return $result;
				}, $scores);
				usort($scores, function($a, $b)
				{
					if($a[2] == $b[2])
						return 0;
					else if($a[2] < $b[2])
						return -1;
					else
						return 1;
				});

				foreach($scores as $i => $line)
				{
					?>
			<tr>
				<td><?= $i + 1 ?></td>
				<td><?= sprintf("%.2f", $line[2]) ?></td>
				<td><?= $line[0] ?></td>
				<td><?= $line[1] ?></td>
			</tr>
					<?php
				}
			?>
	</body>
</html>
